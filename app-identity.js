function startDni(forceMatch=false){openFlow(forceMatch?'dni_match':'dni',forceMatch?'Validar DNI + nombre':'Identidad');bot(forceMatch?'Pásame el DNI y el nombre declarado. Yo compararé ambos.':'¿Quieres consultar solo el DNI o validar también el nombre?','Vamos con identidad.');if(!forceMatch){actions(`<div class="grid2"><button class="choice" id="dniOnly"><strong>🪪 Solo DNI</strong><small>Traer identidad disponible</small></button><button class="choice" id="dniWithName"><strong>✅ DNI + nombre</strong><small>Validar coincidencia</small></button></div>`);$('dniOnly').onclick=()=>dniForm(false);$('dniWithName').onclick=()=>dniForm(true)}else dniForm(true)}
function dniForm(match){progress(25);actions(`<div class="form"><label class="field"><span>DNI</span><input id="dniVal" inputmode="numeric" maxlength="8" placeholder="8 dígitos"></label>${match?'<label class="field"><span>Nombre declarado</span><input id="dniName" placeholder="Nombres y apellidos"></label>':''}<button class="primary" id="dniGo">Consultar</button></div>`);$('dniGo').onclick=async()=>{const dni=$('dniVal').value.replace(/\D/g,'');const nombre=match?$('dniName').value.trim():'';if(dni.length!==8)return toast('DNI debe tener 8 dígitos');user(match?`${dni} · ${nombre}`:dni);actions('');progress(55);setRod('thinking','Consultando identidad…');let res;try{if(apiEnabled())res=await api('/api/dni',{json:{dni,nombre_declarado:nombre}});else{await demoDelay();res={ok:true,dni,nombre:'APELLIDO PATERNO APELLIDO MATERNO NOMBRES',human_status:match?'COINCIDE':'DNI ENCONTRADO',match:match?true:null,similarity:match?0.97:null}}}catch(e){setRod('error','No pude consultar Factiliza.');bot(`<span class="svcStatus bad">ERROR</span><br><br>${safe(humanError(e))}`);return}progress(100);setRod('', 'Identidad lista.');const ok=res.ok!==false;bot(`<div class="resultBox"><span class="svcStatus ${ok?'ok':'bad'}">${safe(res.human_status||res.status||'RESULTADO')}</span><br><br><b>${safe(res.nombre||'')}</b><br>${match&&res.similarity!=null?`Similitud: ${Math.round(res.similarity*100)}%<br>`:''}<small>${apiEnabled()?'Consulta real vía ROD API':'Resultado demo hasta configurar ROD API'}</small></div>`,res.human_status||'Consulta terminada');addHistory('🪪',match?'DNI + nombre':'Consulta DNI',dni,res.human_status||res.status||'OK');addResult('Identidad '+dni,res.human_status||res.status||'OK',JSON.stringify(res,null,2));finishButtons(()=>startDni(match))}}
function startRuc(match=false){
  openFlow(match?'ruc_match':'ruc',match?'RUC + razón social':'Consulta RUC');
  bot(match?'Pásame el RUC y la razón social declarada.':'Pásame el RUC. Consultaré SUNAT en segundo plano.','Vamos con RUC.');
  actions(`<div class="form"><label class="field"><span>RUC</span><input id="rucVal" inputmode="numeric" maxlength="11" placeholder="11 dígitos"></label>${match?'<label class="field"><span>Razón social declarada</span><input id="rucName" placeholder="Razón social"></label>':''}<button class="primary" id="rucGo">Consultar SUNAT</button></div>`);
  $('rucGo').onclick=async()=>{
    const ruc=$('rucVal').value.replace(/\D/g,'');
    const razonDeclarada=match?$('rucName').value.trim():'';
    if(ruc.length!==11)return toast('RUC debe tener 11 dígitos');
    if(match&&!razonDeclarada)return toast('Escribe la razón social declarada');
    user(match?`${ruc} · ${razonDeclarada}`:ruc);
    actions('');progress(55);setRod('thinking','Consultando SUNAT…');
    let res;
    try{
      if(apiEnabled()){
        res=await api('/api/ruc',{json:{ruc,razon_social_declarada:razonDeclarada}});
      }else{
        await demoDelay(650);
        res={ok:true,ruc,razon_social:'EMPRESA DEMOSTRACIÓN S.A.C.',estado:'ACTIVO',condicion:'HABIDO',domicilio_fiscal:'LIMA - PERÚ',similarity:match?0.96:null,match:match?true:null,human_match_status:match?'COINCIDE':'SIN COMPARACIÓN'};
      }
    }catch(e){
      setRod('error','SUNAT no respondió.');
      bot(`<span class="svcStatus bad">ERROR</span><br><br>${safe(humanError(e))}`);
      return;
    }
    progress(82);setRod('', 'RUC encontrado.');
    const matchLine=match&&res.similarity!=null?`<br>Comparación: <b>${safe(res.human_match_status||'')}</b> · ${Math.round(res.similarity*100)}%`:'';
    bot(`<span class="svcStatus ${res.ok!==false?'ok':'bad'}">${res.ok!==false?'RUC ENCONTRADO':'REVISAR'}</span><br><br><b>${safe(res.razon_social||'')}</b><br>RUC: ${safe(res.ruc||ruc)}<br>Estado: <b>${safe(res.estado||'—')}</b><br>Condición: <b>${safe(res.condicion||'—')}</b><br>Domicilio: ${safe(res.domicilio_fiscal||'—')}${matchLine}<br><small>${apiEnabled()?'SUNAT Web en backend':'Demo hasta configurar backend'}</small>`);
    state.data.ruc=ruc;state.data.razon=res.razon_social||'';
    actions(`<div class="grid3"><button class="choice" id="rucReps"><strong>👥 Representantes</strong><small>Solo si los necesitas</small></button><button class="choice" id="rucSave"><strong>📥 Guardar</strong><small>Agregar resultado</small></button><button class="primary" id="rucEnd">✓ Finalizar</button></div>`);
    $('rucReps').onclick=()=>queryReps(ruc,state.data.razon);
    $('rucSave').onclick=()=>{addResult('RUC '+ruc,res.razon_social||'Consulta SUNAT',JSON.stringify(res,null,2));toast('Resultado guardado')};
    $('rucEnd').onclick=()=>{addHistory('🏢',match?'RUC + razón social':'Consulta RUC',ruc,match?(res.human_match_status||res.estado||'OK'):(res.estado||'OK'));closeFlow()};
  };
}
function startReps(){openFlow('reps','Representantes legales');bot('Pásame el RUC. Solo consultaré representantes cuando tú lo pidas.');actions(`<div class="form"><label class="field"><span>RUC</span><input id="repRuc" maxlength="11" inputmode="numeric"></label><button class="primary" id="repGo">Consultar representantes</button></div>`);$('repGo').onclick=()=>queryReps($('repRuc').value.replace(/\D/g,''),'')}
async function queryReps(ruc,razon){if(ruc.length!==11)return toast('RUC debe tener 11 dígitos');user('Consultar representantes de '+ruc);actions('');progress(60);setRod('thinking','Buscando representantes…');let res;try{if(apiEnabled())res=await api('/api/ruc/representatives',{json:{ruc,razon_social:razon}});else{await demoDelay();res={ok:true,count:2,representantes:[{doc_tipo:'DNI',doc_num:'********',nombre:'ANA TORRES RAMÍREZ',cargo:'GERENTE GENERAL',fecha_desde:'2024-01-01'},{doc_tipo:'DNI',doc_num:'********',nombre:'CARLOS VEGA DÍAZ',cargo:'APODERADO',fecha_desde:'2024-01-01'}]}}}catch(e){setRod('error','No pude leer representantes.');bot(`<span class="svcStatus bad">ERROR</span><br>${safe(humanError(e))}`);return}progress(100);setRod('', 'Representantes listos.');const reps=res.representantes||[];bot(`<span class="svcStatus ok">${reps.length} REPRESENTANTE(S)</span><br><br>${reps.length?reps.map(x=>`• <b>${safe(x.nombre)}</b> — ${safe(x.cargo)}<br>`).join(''):'SUNAT no devolvió representantes legibles.'}`);addHistory('👥','Representantes',ruc,String(reps.length));addResult('Representantes '+ruc,`${reps.length} encontrados`,JSON.stringify(res,null,2));finishButtons(()=>startReps())}
