"""Frozen-model development diagnostics; no fitting or provider acquisition."""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from itertools import combinations

import numpy as np

from defensive_network_disruption.geometry.attenuation import summed_segment_attenuation
from defensive_network_disruption.geometry.segment import point_to_segment_distance
from defensive_network_disruption.validation.ranking_features import choice_features
from defensive_network_disruption.validation.ranking_metrics import expected_credits

TOLERANCE = 1e-12
POPULATION_SHA = 'cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d'
FEATURES = ('distance','longitudinal','absolute_lateral','receiver_distance','segment_distance','attenuation')
COMPONENTS = ('attacking','receiver','segment','attenuation')


@dataclass(frozen=True)
class Geometry:
    carrier_xy: tuple
    candidate_xy: tuple
    defender_xy: tuple


def feature_matrices(geometry):
    m0,_ = choice_features(geometry,'m0')
    m1,_ = choice_features(geometry,'m1')
    attenuation = [summed_segment_attenuation(geometry.defender_xy,geometry.carrier_xy,r) for r in geometry.candidate_xy]
    m2=np.column_stack((m1,attenuation))
    if not np.array_equal(m0,m1[:,:3]) or not np.array_equal(m1,m2[:,:5]):
        raise ValueError('raw nesting mismatch')
    mass=[]
    for receiver in geometry.candidate_xy:
        distances=sorted(point_to_segment_distance(d,geometry.carrier_xy,receiver)[0] for d in geometry.defender_xy)
        mass.append(math.fsum(math.exp(-d/5.0) for d in distances[1:]))
    return {'m0':m0,'m1':m1,'m2':m2},float(np.mean(mass))


def quantiles(values,weights,probabilities=(.05,.25,.5,.75,.95)):
    x=np.asarray(values,dtype=float);w=np.asarray(weights,dtype=float)
    if len(x)!=len(w) or not len(x) or not np.isfinite(x).all() or not np.isfinite(w).all() or np.any(w<=0):
        raise ValueError('nonempty finite weighted observations required')
    order=np.argsort(x,kind='stable');x=x[order];w=w[order]
    cumulative=np.cumsum(w);total=cumulative[-1]
    return [float(x[min(int(np.searchsorted(cumulative,p*total,side='left')),len(x)-1)]) for p in probabilities]


def distribution(values,weights):
    if not len(values):return {'count':0,'mean':None,'minimum':None,'maximum':None,'quantiles':None}
    x=np.asarray(values,dtype=float);w=np.asarray(weights,dtype=float)
    qs=quantiles(x,w)
    return {'count':len(x),'mean':float(np.sum(x*w)/np.sum(w)),'minimum':float(np.min(x)),'maximum':float(np.max(x)), 'quantiles':dict(zip(('q05','q25','q50','q75','q95'),qs))}


def strata_values(matrix):
    return np.column_stack((matrix[:,0],matrix[:,1],np.abs(matrix[:,2]),matrix[:,3:]))


def prepare_cuts(geometries):
    """Input is alias -> Geometry list; targets cannot enter this interface."""
    values=[];weights=[];state_values=[];state_weights=[]
    for alias in sorted(geometries):
        rows=geometries[alias]
        for geo in rows:
            matrices,mass=feature_matrices(geo);x=strata_values(matrices['m2'])
            values.extend(x.tolist());weights.extend([1/len(geometries)/len(rows)/len(x)]*len(x))
            state_values.append(mass);state_weights.append(1/len(geometries)/len(rows))
    x=np.asarray(values)
    cuts={name:sorted(set(quantiles(x[:,i],weights,(.25,.5,.75)))) for i,name in enumerate(FEATURES)}
    cuts['nonnearest_mass']=sorted(set(quantiles(state_values,state_weights,(.25,.5,.75))))
    return cuts


def bin_name(value,cuts):return 'bin_'+str(int(np.searchsorted(cuts,value,side='left'))+1)


def direction(length,dx):
    if length<=1e-9:return 'degenerate'
    ratio=dx/length
    if ratio>math.sin(math.radians(10)):return 'forward'
    if ratio< -math.sin(math.radians(10)):return 'backward'
    return 'approximately_lateral'


def rank_blocks(utilities):
    u=np.asarray(utilities,dtype=float)
    if not len(u) or not np.isfinite(u).all():raise ValueError('finite nonempty utility required')
    order=np.argsort(-u,kind='stable');ranks=np.empty(len(u));blocks=np.empty(len(u),dtype=int)
    start=0;block=0;top=[]
    while start<len(u):
        end=start+1
        while end<len(u) and u[order[start]]-u[order[end]]<=TOLERANCE:end+=1
        for i in order[start:end]:ranks[i]=(start+1+end)/2;blocks[i]=block
        if start==0:top=sorted(int(i) for i in order[start:end])
        start=end;block+=1
    return {'ranks':ranks.tolist(),'blocks':blocks.tolist(),'top':top}


def pair_comparison(left,right,indices=None):
    pairs=list(combinations(range(len(left)),2)) if indices is None else indices
    out={'pairs':len(pairs),'unchanged':0,'strict_reversal':0,'tie_created':0,'tie_removed':0}
    for i,j in pairs:
        a=int(np.sign(left[i]-left[j]));b=int(np.sign(right[i]-right[j]))
        if a==b:out['unchanged']+=1
        elif a and b:out['strict_reversal']+=1
        elif b==0:out['tie_created']+=1
        else:out['tie_removed']+=1
    out['changed_fraction']=None if not pairs else 1-out['unchanged']/len(pairs)
    return out


def disagreement(matrix):
    eligible=[];discordant=[]
    for i,j in combinations(range(len(matrix)),2):
        a=matrix[i,3]-matrix[j,3];b=matrix[i,4]-matrix[j,4]
        if abs(a)<=TOLERANCE or abs(b)<=TOLERANCE:continue
        eligible.append((i,j))
        if (a>0)!=(b>0):discordant.append((i,j))
    return eligible,discordant


def decompose(matrix,authority):
    mean,scale,beta=(np.asarray(authority[k],dtype=float) for k in ('mean','scale','coefficients'))
    if matrix.shape[1]!=len(beta) or np.any(scale<=0):raise ValueError('model dimensions or scales invalid')
    z=(matrix-mean)/scale;u=z@beta;c=z*beta
    residual=np.abs(np.sum(c,axis=1)-u)
    bounds=8*matrix.shape[1]*np.finfo(float).eps*np.maximum(1,np.maximum(np.sum(np.abs(c),axis=1),np.abs(u)))
    if not np.isfinite(u).all() or np.any(residual>bounds):raise ValueError('utility reconstruction failure')
    grouped=np.zeros((len(matrix),4));grouped[:,0]=c[:,:3].sum(axis=1)
    if matrix.shape[1]>=5:grouped[:,1:3]=c[:,3:5]
    if matrix.shape[1]==6:grouped[:,3]=c[:,5]
    return u,c,grouped,float(np.max(residual))


def diagnose(geometry,target_index,models,ordinal,alias):
    matrices,mass=feature_matrices(geometry)
    if target_index is None or not 0<=target_index<len(geometry.candidate_xy):raise ValueError('authoritative target required')
    results={};raw_columns={};residual=0
    for model in ('m0','m1','m2'):
        u,c,grouped,error=decompose(matrices[model],models[model]);raw_columns[model]=c
        residual=max(residual,error);blocks=rank_blocks(u)
        # Oracle is the unchanged tie-aware metric helper, not a new rank sorter.
        credit=expected_credits(u,target_index)
        block=blocks['blocks'][target_index]
        first=1+sum(b<block for b in blocks['blocks']);last=sum(b<=block for b in blocks['blocks'])
        oracle=sum(1/position for position in range(first,last+1))/(last-first+1)
        if credit['rr']!=oracle:raise ValueError('tie oracle mismatch')
        results[model]={**blocks,'target_rank':blocks['ranks'][target_index],'utility':u.tolist(),'components':grouped.tolist(),'centered_components':(grouped-grouped.mean(axis=0)).tolist()}
    for left,right,width in (('m0','m1',3),('m1','m2',5)):
        if not np.array_equal(models[left]['mean'],models[right]['mean'][:width]) or not np.array_equal(models[left]['scale'],models[right]['scale'][:width]):raise ValueError('frozen preprocessing nesting mismatch')
    eligible,discordant=disagreement(matrices['m1'])
    common={}
    for left,right in (('m0','m1'),('m1','m2')):
        width=raw_columns[left].shape[1]
        shared=(raw_columns[right][:,:width]-raw_columns[left]).sum(axis=1)
        added=raw_columns[right][:,width:].sum(axis=1)
        delta=np.array(results[right]['utility'])-np.array(results[left]['utility'])
        bound=8*12*np.finfo(float).eps*np.maximum(1,np.sum(np.abs(raw_columns[right]),axis=1)+np.sum(np.abs(raw_columns[left]),axis=1))
        if np.any(np.abs(shared+added-delta)>bound):raise ValueError('between-model accounting mismatch')
        common[right+'_'+left]={'shared':shared.tolist(),'added':added.tolist(),'centered_shared':(shared-shared.mean()).tolist(),'centered_added':(added-added.mean()).tolist()}
    return {'ordinal':ordinal,'alias':alias,'tie_key':hashlib.sha256((POPULATION_SHA+':'+str(ordinal)).encode()).hexdigest(),'target_index':target_index,'features':strata_values(matrices['m2']).tolist(),'direction':direction(matrices['m2'][target_index,0],matrices['m2'][target_index,1]),'nonnearest_mass':mass,'models':results,'bookkeeping':common,'eligible_pairs':len(eligible),'discordant_pairs':len(discordant),'disagreement_fraction':len(discordant)/len(eligible) if eligible else None,'disagreement_order':pair_comparison(results['m0']['blocks'],results['m1']['blocks'],discordant),'m1_m0_pairs':pair_comparison(results['m0']['blocks'],results['m1']['blocks']),'m2_m1_pairs':pair_comparison(results['m1']['blocks'],results['m2']['blocks']),'m1_delta':results['m1']['target_rank']-results['m0']['target_rank'],'m2_delta':results['m2']['target_rank']-results['m1']['target_rank'],'max_reconstruction_residual':residual}


def select_cases(rows):
    selected=[];used=set();match_counts={};counts={k:0 for k in ('failure','feature_disagreement','m2_ordering_change','agreement')}
    def take(pool,quota,category,key):
        for row in sorted(pool,key=key):
            if quota==0:break
            if row['ordinal'] in used or match_counts.get(row['alias'],0)>=2:continue
            selected.append({'ordinal':row['ordinal'],'alias':row['alias'],'category':category,'tie_key':row['tie_key']});used.add(row['ordinal']);match_counts[row['alias']]=match_counts.get(row['alias'],0)+1;counts[category]+=1;quota-=1
    take([r for r in rows if r['m1_delta']>=2],2,'failure',lambda r:(-r['m1_delta'],r['tie_key']))
    take([r for r in rows if r['m2_delta']>=2],1,'failure',lambda r:(-r['m2_delta'],r['tie_key']))
    take([r for r in rows if r['disagreement_fraction'] is not None and r['disagreement_fraction']>0 and r['models']['m0']['top']!=r['models']['m1']['top']],3,'feature_disagreement',lambda r:(-r['disagreement_fraction'],r['tie_key']))
    take([r for r in rows if r['models']['m1']['top']!=r['models']['m2']['top']],3,'m2_ordering_change',lambda r:(-r['m2_m1_pairs']['changed_fraction'],-abs(r['m2_delta']),r['tie_key']))
    take([r for r in rows if r['models']['m0']['top']==r['models']['m1']['top']==r['models']['m2']['top']==[r['target_index']]],3,'agreement',lambda r:r['tie_key'])
    selected.sort(key=lambda r:r['tie_key'])
    for i,row in enumerate(selected,1):row['case_id']=f'case_{i:02d}'
    return selected,counts
