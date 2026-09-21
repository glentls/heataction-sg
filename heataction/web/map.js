/* Local SVG map of official polygons. No external tiles, CDN, or location tracking. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number = value => value === null || value === undefined ? 'Unavailable' : value.toLocaleString('en-SG');
  const clock = value => value ? new Date(value).toLocaleString('en-SG', {timeZone:'Asia/Singapore',hour12:false}) + ' SGT' : 'Unavailable';
  const ns = 'http://www.w3.org/2000/svg';
  let geography = null, plan = null, loading = false, selected = 'am', projection = null;
  const paths = new Map();
  const populationColours = ['#e0eee5','#adcfbb','#6eaa8e','#37826a','#12634f'];
  const heatColours = {Low:'#b2d9ba',Moderate:'#f2ce6d',High:'#e28668',Unknown:'#dce2e3'};
  function node(tag, attributes) {
    const result = document.createElementNS(ns, tag);
    for (const [name,value] of Object.entries(attributes)) result.setAttribute(name,value);
    return result;
  }
  function project(point) {return [(point[0]-projection.west)*projection.scale+20,(projection.north-point[1])*projection.scale+20];}
  function rings(geometry) {return geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;}
  function rowFor(id) {return plan?.rows.find(row => row.area_id === id);}
  function select(id) {selected=id;byId('mapArea').value=id;render();}
  function build() {
    const features = geography.geojson.features;
    const boxes = features.map(f => f.properties.bounds);
    const west=Math.min(...boxes.map(b=>b[0])),east=Math.max(...boxes.map(b=>b[2]));
    const south=Math.min(...boxes.map(b=>b[1])),north=Math.max(...boxes.map(b=>b[3]));
    projection={west,north,scale:Math.min(760/(east-west),390/(north-south))};
    const svg=byId('areaMap');
    const group=node('g', {'aria-label':'Planning areas'});
    for (const feature of features) {
      const p=feature.properties;
      const d=rings(feature.geometry).map(poly=>poly.map(ring=>ring.map((point,i)=>{
        const [x,y]=project(point);return `${i?'L':'M'}${x.toFixed(2)},${y.toFixed(2)}`;
      }).join('')+'Z').join('')).join('');
      const path=node('path',{d,'fill-rule':'evenodd',class:'map-area',tabindex:'0',role:'button','aria-label':p.name,'data-area':p.area_id});
      const title=node('title',{});title.textContent=p.name;path.append(title);
      path.addEventListener('click',()=>select(p.area_id));
      path.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();select(p.area_id);}});
      paths.set(p.area_id,path);group.append(path);
    }
    svg.append(group);
    const stations=node('g',{'aria-label':'Pilot WBGT station reference locations'});
    for(const area of geography.areas){
      const [cx,cy]=project([area.station_longitude,area.station_latitude]);
      const dot=node('circle',{cx,cy,r:4,class:'station-marker',role:'button',tabindex:'0','aria-label':`${area.station_name}, ${area.station_id}; inspect ${area.name}`});
      const title=node('title',{});title.textContent=`${area.station_id}: ${area.station_name} (reviewed reference location)`;dot.append(title);
      dot.addEventListener('click',()=>select(area.area_id));
      dot.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();select(area.area_id);}});
      const label=node('text',{x:cx+7,y:cy-7,class:'map-station-label','aria-hidden':'true'});label.textContent=area.name;
      stations.append(dot,label);
    }
    svg.append(stations);
    byId('mapArea').innerHTML=[...features].sort((a,b)=>a.properties.name.localeCompare(b.properties.name)).map(f=>`<option value="${escape(f.properties.area_id)}">${escape(f.properties.name)}${f.properties.pilot?' · Pilot':''}</option>`).join('');
    byId('mapArea').value=selected;
    byId('mapArea').addEventListener('change',event=>select(event.target.value));
    byId('mapLayer').addEventListener('change',render);
    byId('mapReset').addEventListener('click',()=>svg.setAttribute('viewBox','0 0 800 430'));
    byId('mapZoom').addEventListener('click',()=>{
      const box=features.find(f=>f.properties.area_id===selected).properties.bounds;
      const [left,top]=project([box[0],box[3]]),[right,bottom]=project([box[2],box[1]]);
      const width=Math.max(right-left,30)+35,height=Math.max(bottom-top,20)+35;
      svg.setAttribute('viewBox',`${left-17.5} ${top-17.5} ${width} ${height}`);
    });
    byId('mapProvenance').innerHTML='Sources: '+geography.sources.map(source=>`<a href="${escape(source.source_url)}" target="_blank" rel="noreferrer">${source.vintage===2020?'SingStat Census 2020':'URA Master Plan 2019'}</a>`).join(' · ')+
      ` · <a href="${escape(geography.license_url)}" target="_blank" rel="noreferrer">Singapore Open Data Licence</a>. All 55 boundaries are shown; planning is limited to the three outlined pilot areas.`;
  }
  function colour(properties) {
    if(byId('mapLayer').value==='heat')return properties.pilot ? heatColours[rowFor(properties.area_id)?.category || 'Unknown'] : '#f1f3f2';
    const share=properties.senior_share;
    return share===null || share===undefined ? '#dce2e3' : populationColours[share<.10?0:share<.15?1:share<.20?2:share<.25?3:4];
  }
  function explanation(row) {
    if(!row)return 'Current plan unavailable. Refresh stored observations to try again.';
    if(!row.eligible)return 'Excluded from your selected service areas. Its population remains in the fixed three-area reference cohort.';
    if(row.status!=='Ready')return `${row.status}. No heat-based assignment is made until data and mapping checks pass.`;
    if(row.assigned)return `Assigned one team slot: its heat and demographic priority ranks within your budget. Capacity is ${number(row.contact_capacity)} assumed contacts, not completed outreach.`;
    if(row.category==='Low')return 'The station proxy is in the Low category, giving zero additional heat priority under the current policy.';
    if(plan.budget===0)return 'No assignment because the team budget is zero.';
    return 'Not assigned within the current budget; higher-ranked selected areas take the available slots.';
  }
  function detail(feature) {
    const p=feature.properties,row=rowFor(p.area_id),area=geography.areas.find(a=>a.area_id===p.area_id);
    const max=Math.max(1,...(p.age_bands||[]).map(b=>b.count||0));
    const bands=(p.age_bands||[]).map((band,i)=>`<div class="age-band"><span>${escape(band.label)}</span><div class="age-track"><div class="age-fill ${i>=13?'senior':''}" style="width:${band.count===null?0:band.count/max*100}%"></div></div><span>${band.count===null?'—':number(band.count)}</span></div>`).join('');
    let weather='';
    if(area){
      const fresh=row?.status==='Ready';
      weather=`<div class="detail-weather"><span class="pilot-badge">WBGT STATION PROXY</span><p><strong>${escape(area.station_name)}</strong><br>${escape(area.station_id)} · ${area.mapping_distance_km.toFixed(2)} km from boundary-box centre</p>
        <span class="tag ${fresh?row.category.toLowerCase():'unknown'}">${fresh?`${row.forecast_wbgt.toFixed(1)} °C WBGT · ${escape(row.category)}`:escape(row?.status||'Plan unavailable')}</span>
        <small>Observed: ${clock(row?.observed_at)}${row?.observation_age_minutes!==null&&row?.observation_age_minutes!==undefined?` · ${Math.max(0,Math.floor(row.observation_age_minutes))} min old`:''}</small>
        <p>One-hour persistence baseline. This station does not measure conditions everywhere inside the area.</p>
        <div class="detail-explanation">${escape(explanation(row))}</div>
        ${row?`<button id="toggleMapArea" type="button" class="secondary" style="margin-top:10px">${row.eligible?'Exclude from':'Include in'} service areas</button>`:''}
        </div>`;
    }else weather='<div class="detail-explanation">Outside the three-area pilot. Demographics are shown for context; no reviewed station mapping or outreach recommendation is configured here.</div>';
    byId('areaDetail').innerHTML=`<span class="pilot-badge">${p.pilot?'PILOT AREA':'CONTEXT AREA'}</span><h3>${escape(p.name)}</h3><span class="detail-region">${escape(p.region)}</span>
      <div class="detail-count">${number(p.seniors65)}<small>residents aged 65+ · Census 2020</small></div>
      <div class="detail-share">${p.senior_share===null||p.senior_share===undefined?'Share unavailable':(p.senior_share*100).toFixed(1)+'% of residents'}</div>
      <small>Total residents: ${number(p.residents)} · published rounded counts</small>
      <details><summary>Age profile (2020)</summary><div class="age-profile">${bands||'No published age profile available.'}</div><small>Bars use total-sex age bands once. Missing bands are not treated as zero.</small></details>
      ${weather}
      <details class="detail-sources"><summary>Sources &amp; mapping review</summary>
      <p>Census row: ${escape(p.population_row||'Unavailable')}<br>Population dataset: ${escape(p.population_dataset_id||'Unavailable')}<br>Boundary dataset: ${escape(p.boundary_dataset_id)}<br>Boundary code: ${escape(p.boundary_code)}</p>
      ${area?`<p>Reviewed ${escape(area.mapping_reviewed_at)}. ${escape(area.mapping_review_scope)}</p><p>${escape(area.mapping_review)}</p><p>${escape(area.mapping_method)}</p><p>Station reference observed: ${clock(area.station_reference_observed_at)}</p>`:'<p>Station mapping: not reviewed for this area.</p>'}</details>`;
    byId('toggleMapArea')?.addEventListener('click',()=>{
      const input=[...document.querySelectorAll('#areas input')].find(x=>x.value===p.area_id);
      if(input){input.checked=!input.checked;input.dispatchEvent(new Event('change'));}
    });
  }
  function render() {
    if(!geography)return;
    for(const feature of geography.geojson.features){
      const p=feature.properties,path=paths.get(p.area_id);
      path.setAttribute('fill',colour(p));
      path.setAttribute('class',`map-area${p.pilot?' pilot':''}${p.area_id===selected?' selected':''}`);
      path.setAttribute('aria-pressed',String(p.area_id===selected));
    }
    const items=byId('mapLayer').value==='population' ? populationColours.map((c,i)=>[c,['<10%','10–<15%','15–<20%','20–<25%','25%+'][i]]).concat([['#dce2e3','Unavailable']]) : Object.entries(heatColours).map(([label,c])=>[c,label]).concat([['#f1f3f2','Outside pilot']]);
    byId('mapLegend').innerHTML=items.map(([c,label])=>`<span class="legend-item"><span class="legend-swatch" style="background:${c}"></span>${label}</span>`).join('');
    const ready=plan?.rows.filter(r=>r.status==='Ready').length||0;
    byId('mapStatus').textContent=plan ? `${ready} / ${geography.areas.length} pilot areas have usable mapped weather at ${clock(plan.as_of)}. ${geography.areas.length-ready?'Areas without usable weather receive no heat-based assignment.':''}` : 'Plan request failed. Demographics remain available; weather and assignments are unavailable.';
    detail(geography.geojson.features.find(f=>f.properties.area_id===selected));
  }
  window.heatMap={
    async update(nextPlan){
      plan=nextPlan;
      if(!plan.has_geography){byId('geography').hidden=true;return;}
      byId('geography').hidden=false;
      if(geography){render();return;}
      if(loading)return;
      loading=true;byId('mapStatus').textContent='Loading verified Census and boundary snapshots…';
      try{
        const response=await fetch('/api/geography');
        if(!response.ok)throw new Error('Unable to load geographic reference data. Refresh to retry.');
        const data=await response.json();
        if(data.data_mode!=='observed')throw new Error('Expected observed geographic references.');
        geography=data;build();render();
      }catch(error){byId('mapStatus').textContent=error.message;}
      finally{loading=false;}
    },
    invalidate(){plan=null;render();}
  };
})();
