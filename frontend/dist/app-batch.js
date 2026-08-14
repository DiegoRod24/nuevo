function startBatch(label){
  openFlow(label.toLowerCase(),'Anexo '+label);
  bot(`Sube tu archivo ${label}. Primero revisaré la estructura y luego podrás ejecutar las consultas reales en masivo.`);
  actions(`<div class="form drop"><input id="batchFile" type="file" accept=".xlsx,.xls,.csv"><p style="color:var(--muted)">ROD detecta hojas, DNI/RUC y estructura antes de consultar.</p><button class="primary" id="batchAnalyze">Analizar ${label}</button></div>`);
  $('batchAnalyze').onclick=async()=>{
    const f=$('batchFile').files[0]; if(!f)return toast('Selecciona un Excel');
    if(!apiEnabled()){setRod('alert','Falta conectar ROD API.');bot(`<span class="svcStatus bad">BACKEND NO CONECTADO</span><br><br>El Excel masivo necesita ROD API ejecutándose. Configura <b>API_BASE</b> en config.js con la URL pública del backend.`);return}
    user(f.name); actions(''); progress(12); setRod('thinking','Analizando el archivo…');
    try{
      const form=new FormData(); form.append('file',f);
      const res=await api('/api/batch/'+label.toLowerCase(),{form});
      if(res.ok===false)throw new Error(res.message||'No pude leer el archivo');
      state.data.batchFile=f; state.data.batchInfo=res; state.data.batchLabel=label;
      progress(25); setRod('', 'Archivo analizado.');
      bot(`Detecté <b>${safe(res.detected_type||label)}</b>.<div class="metrics"><div class="metric"><small>Registros</small><b>${res.rows??'—'}</b></div><div class="metric"><small>DNI únicos</small><b>${res.dni_unique??'—'}</b></div><div class="metric"><small>RUC únicos</small><b>${res.ruc_unique??'—'}</b></div><div class="metric"><small>Hojas</small><b>${res.sheets?.length??'—'}</b></div></div>`);
      actions(`<div class="grid2"><button class="primary" id="batchFull">✦ Ejecutar flujo completo REAL</button><button class="choice" id="batchSelect"><strong>☷ Elegir módulos</strong><small>Personaliza qué consultar</small></button></div>`);
      $('batchFull').onclick=()=>runMassive(label,res,f,{dni:true,ruc:true,cpe:label==='4D',representatives:false,pj_queue:true});
      $('batchSelect').onclick=()=>selectBatchModules(label,res,f);
    }catch(e){setRod('error','No pude leer el archivo.');bot(`<span class="svcStatus bad">ERROR</span><br>${safe(humanError(e))}`)}
  }
}

function selectBatchModules(label,res,file){
  user('Elegir módulos');
  bot('Marca lo que necesitas. ROD reutilizará DNI/RUC repetidos y consultará una sola vez cada dato único.');
  actions(`<div class="form">
    <label><input id="modDni" type="checkbox" checked> DNI / identidad · Factiliza</label><br>
    <label><input id="modRuc" type="checkbox" checked> RUC / razón social · SUNAT</label><br>
    ${label==='4D'?'<label><input id="modCpe" type="checkbox" checked> Comprobantes · SUNAT API</label><br><label><input id="modReps" type="checkbox"> Representantes legales</label><br>':''}
    <label><input id="modPj" type="checkbox" checked> Preparar cola para Poder Judicial</label><br>
    <button class="primary" id="modsGo" style="margin-top:12px">Procesar selección REAL</button>
  </div>`);
  $('modsGo').onclick=()=>runMassive(label,res,file,{
    dni:$('modDni')?.checked??true,
    ruc:$('modRuc')?.checked??true,
    cpe:label==='4D'&&($('modCpe')?.checked??true),
    representatives:label==='4D'&&($('modReps')?.checked??false),
    pj_queue:$('modPj')?.checked??true
  });
}

function massiveSteps(label){
  return label==='4D'
    ?['Lectura / prevalidación','DNI · Factiliza','RUC · SUNAT','Comprobantes · SUNAT API','Representantes','Cola Poder Judicial','Excel final']
    :['Lectura / prevalidación','DNI · Factiliza','RUC · SUNAT','Clasificación','Cola Poder Judicial','Excel final'];
}

function stageIndex(label,stage=''){
  const s=String(stage).toUpperCase();
  if(s.includes('GENERANDO EXCEL')||s.includes('TERMINADO'))return massiveSteps(label).length-1;
  if(s.includes('REPRESENTANTE'))return label==='4D'?4:3;
  if(s.includes('CPE'))return label==='4D'?3:2;
  if(s.includes('RUC'))return 2;
  if(s.includes('DNI')||s.includes('FACTILIZA'))return 1;
  return 0;
}

function renderLiveJob(label,job){
  const steps=massiveSteps(label),active=stageIndex(label,job.stage);
  const c=job.counts||{};
  const metrics=job.total?`<div class="metrics"><div class="metric"><small>Procesados</small><b>${job.processed||0}/${job.total}</b></div><div class="metric"><small>Progreso</small><b>${job.progress||0}%</b></div><div class="metric"><small>Correctos</small><b>${c.correct??'—'}</b></div><div class="metric"><small>Observados</small><b>${c.observed??'—'}</b></div></div>`:'';
  return `<div class="steps">${steps.map((s,i)=>`<div class="step ${i<active?'done':i===active?'run':''}"><i></i>${s}</div>`).join('')}</div>${metrics}<p style="color:var(--muted);margin:12px 0 0">${safe(job.stage||'Procesando…')}</p>`;
}

async function runMassive(label,res,file,options){
  if(!apiEnabled()){setRod('alert','ROD API no está conectada.');bot('No puedo ejecutar consultas reales hasta que API_BASE apunte al backend.');return}
  user('Ejecutar consultas masivas'); actions(''); progress(28); setRod('thinking',`Procesando ${label} en masivo…`);
  bot(`<div id="massiveLive">Preparando trabajo masivo…</div>`);
  try{
    const form=new FormData(); form.append('file',file);
    const q=new URLSearchParams({mode:label,dni:String(!!options.dni),ruc:String(!!options.ruc),cpe:String(!!options.cpe),representatives:String(!!options.representatives),pj_queue:String(!!options.pj_queue)});
    let job=await api('/api/jobs/massive?'+q.toString(),{form});
    const jobId=job.job_id; if(!jobId)throw new Error('El backend no devolvió job_id');
    while(true){
      await new Promise(r=>setTimeout(r,1300));
      job=await api('/api/jobs/'+encodeURIComponent(jobId),{method:'GET'});
      progress(Math.max(28,job.progress||0));
      const live=$('massiveLive'); if(live)live.innerHTML=renderLiveJob(label,job);
      setRod('thinking',job.stage||`Procesando ${label}…`);
      if(job.status==='DONE')break;
      if(job.status==='ERROR')throw new Error(job.error||'El proceso masivo terminó con error');
    }
    progress(100); setRod('',`${label} terminado.`);
    const c=job.counts||{};
    const live=$('massiveLive');
    if(live)live.innerHTML=`<div class="resultBox"><span class="svcStatus ok">PROCESO REAL TERMINADO</span><br><br><b>${c.rows??job.total??0} registros procesados</b><br>✅ ${c.correct??0} correctos<br>⚠️ ${c.observed??0} observados<br>🔄 ${c.technical??0} pendientes técnicos<br>🪪 ${c.dni_unique??0} DNI únicos<br>🏢 ${c.ruc_unique??0} RUC únicos${label==='4D'?`<br>🧾 ${c.cpe_unique??0} comprobantes únicos`:''}<br>⚖️ ${c.pj_pending??0} listos para PJ</div>`;
    bot('Ya generé el Excel final. El <b>CONTROL_INTERNO</b> queda oculto dentro del archivo y el usuario ve primero las hojas limpias.');
    const downloadUrl=API+'/api/jobs/'+encodeURIComponent(jobId)+'/download';
    actions(`<div class="grid3"><button class="primary" id="downloadXlsx">📥 Descargar Excel</button><button class="choice" id="again"><strong>🔄 Otro archivo</strong></button><button class="choice" id="endFlow"><strong>✓ Finalizar</strong></button></div>`);
    $('downloadXlsx').onclick=()=>window.open(downloadUrl,'_blank');
    $('again').onclick=()=>startBatch(label); $('endFlow').onclick=closeFlow;
    addHistory(label==='4D'?'📑':'📊','Anexo '+label,`${c.rows??job.total??0} registros`,`${c.observed??0} observados · ${c.technical??0} técnicos`);
    addResult('Resultado '+label,`${c.correct??0} correctos · ${c.observed??0} observados`,JSON.stringify({job_id:jobId,counts:c,download:downloadUrl},null,2));
  }catch(e){progress(100);setRod('error','El proceso masivo se detuvo.');bot(`<span class="svcStatus bad">ERROR</span><br><br>${safe(humanError(e))}<br><br><small>ROD no marca esto como observación del usuario: es una falla técnica para revisar/reintentar.</small>`);finishButtons(()=>startBatch(label))}
}

function startDetect(pre=false){
  openFlow(pre?'prevalidate':'detect',pre?'ROD Check':'Déjaselo a ROD');
  bot(pre?'Sube el Excel y revisaré su estructura antes de cualquier consulta.':'Pásame el Excel. Intentaré reconocer si parece 4B, 4D u otro formato.');
  actions(`<div class="form drop"><input id="detectFile" type="file" accept=".xlsx,.xls,.csv"><button class="primary" id="detectGo" style="margin-top:12px">${pre?'Prevalidar':'Detectar archivo'}</button></div>`);
  $('detectGo').onclick=async()=>{
    const f=$('detectFile').files[0];if(!f)return toast('Selecciona un archivo');if(!apiEnabled())return bot('ROD API no está conectada. Esta función requiere backend para analizar el Excel.');
    user(f.name);actions('');progress(45);setRod('thinking','Leyendo estructura…');
    try{const form=new FormData();form.append('file',f);const res=await api('/api/files/detect',{form});progress(100);setRod('',`Parece un ${res.detected_type}.`);bot(`Por la estructura, este archivo parece: <b>${safe(res.detected_type)}</b>.<br><br>Registros: ${res.rows??'—'} · DNI: ${res.dni_unique??'—'} · RUC: ${res.ruc_unique??'—'}`);actions(`<div class="grid2">${['4B','4D'].includes(res.detected_type)?`<button class="primary" id="openDetected">Abrir como ${res.detected_type}</button>`:''}<button class="choice" id="detectEnd">✓ Finalizar</button></div>`);if($('openDetected'))$('openDetected').onclick=()=>startBatch(res.detected_type);$('detectEnd').onclick=closeFlow}catch(e){setRod('error','No pude analizarlo.');bot(`<span class="svcStatus bad">ERROR</span><br>${safe(humanError(e))}`)}
  }
}

function startUtility(f){
  const titles={multi:'Múltiples archivos',compare:'Comparador',retry:'Reprocesar observados',custom:'Flujo personalizado'};openFlow(f,titles[f]);
  if(f==='custom'){bot('Elige los módulos que quieres combinar.');actions(`<div class="form"><label><input type="checkbox" checked> DNI / identidad</label><br><label><input type="checkbox" checked> RUC / SUNAT</label><br><label><input type="checkbox"> Comprobantes</label><br><label><input type="checkbox"> Representantes</label><br><label><input type="checkbox"> Poder Judicial</label><br><button class="primary" id="customGo" style="margin-top:12px">Crear flujo</button></div>`);$('customGo').onclick=()=>{user('Flujo seleccionado');bot('Perfecto. Para ejecución masiva usa 4B/4D y elige módulos; ahí ya corre el backend real.');progress(100);finishButtons(()=>startUtility(f))}}
  else{bot(`${f==='multi'?'El motor masivo ya procesa todas las filas del Excel y reutiliza documentos repetidos. El siguiente paso será recibir varios Excel en una sola carga.':f==='compare'?'La comparación declarado vs consultado ya se ejecuta dentro de 4B/4D para DNI y RUC.':'Los fallos técnicos quedan separados de los observados para poder reprocesarlos sin confundir al auditor.'}`);progress(100);finishButtons(()=>startUtility(f))}
}

function finishButtons(repeat){actions(`<div class="grid3"><button class="choice" id="again"><strong>🔄 Repetir</strong></button><button class="choice" id="goResults"><strong>📥 Resultados</strong></button><button class="primary" id="endFlow">✓ Finalizar</button></div>`);$('again').onclick=repeat;$('goResults').onclick=()=>{closeFlow();nav('results')};$('endFlow').onclick=closeFlow}
