import re
from fastapi import FastAPI, HTTPException
from typing import List
from models import Resumo, TextoEntrada, PalavrasChave
from fastapi.responses import Response  
from fastapi.exceptions import RequestValidationError

app = FastAPI()

resumos: List[Resumo] = []

IGNORE_WORDS = {"o", "a", "os", "as", "um", "uma", "uns", "umas", 
             "de", "do", "da", "dos", "das", "em", "no", "na", 
        "nos", "nas", "por", "para", "com", "sem", "que", "e", "é"}


def markdown_para_texto(markdown: str) -> str:
    if not markdown:
        return ""
    
    # Remove apenas se existir, senão retorna o texto original
    removals = [
        (r'#+\s?', ''),                   # Headings
        (r'(\*\*|__)(.*?)\1', r'\2'),      # Bold
        (r'(\*|_)(.*?)\1', r'\2'),         # Italic
        (r'^[-*+]\s+', '', re.MULTILINE),  # List markers
        (r'\[(.*?)\]\(.*?\)', r'\1'),      # Links
        (r'[`>]', '')                      # Code blocks
    ]
    
    texto = markdown
    for pattern, replacement in removals:
        flags = pattern[2] if len(pattern) > 2 else 0
        if isinstance(pattern, tuple) and len(pattern) > 2:
            texto = re.sub(pattern[0], replacement, texto, flags=pattern[2])
        else:
            texto = re.sub(pattern, replacement, texto)
    
    return texto.strip()


def gerar_resumo(texto: str) -> str:

    texto = re.sub(r'[#*_`\-]+', '', texto)   # Remove resquício de sintaxe Markdown

    texto = texto.replace('\n', ' ').strip()     # Normaliza espaços 

    frases = re.split(r'(?<=[.!?])\s+', texto)   # Divide o texto em frases

    resumo = ' '.join(frases[:3])   # Pega as primeiras 3 frases e junta com espaços
    return resumo


def palavras_chave_texto(texto: str) -> List[str]:
    if not texto or not isinstance(texto, str):
        return []
    
    texto_limpo = re.sub(r'[^\w\s]', '', texto.lower())
    palavras = texto_limpo.split()

    contador = {}
    for palavra in palavras:
        if palavra not in IGNORE_WORDS:
            contador[palavra] = contador.get(palavra, 0) + 1

    palavras_ordenadas = []
    for palavra, freq in contador.items(): 
        palavras_ordenadas.append((freq, palavra))
    
    palavras_ordenadas.sort(reverse=True)

    palavras_chave = [palavra for freq, palavra in palavras_ordenadas[:5]] 
    return [palavra.capitalize() for palavra in palavras_chave]



#função para formatar resposta em XML
def formatar_resposta_xml(resumo: str, palavras_chave: List[str]) -> str:
    resumo_xml = f"<resumo>{resumo}</resumo>" if resumo else "<resumo />"
    
    palavras_xml = ""
    if palavras_chave:
        for palavra in palavras_chave:
            palavras_xml += f"<palavra>{palavra}</palavra>"
        palavras_chave_xml = f"<palavras-chave>{palavras_xml}</palavras-chave>"
    else:
        palavras_chave_xml = "<palavras-chave />"
    
    return f"<resposta>{resumo_xml}{palavras_chave_xml}</resposta>"


#endpoint para resposta integrada em XML
@app.post("/processar/", response_class=Response)
def processar_texto(entrada: TextoEntrada):
    try:
        if not entrada.texto.strip():
            raise HTTPException(status_code=400, detail="Erro: o texto de entrada está vazio.")
        
        texto_simples = markdown_para_texto(entrada.texto)
        
        if not texto_simples:
            raise HTTPException(status_code=400, detail="Erro: formato de entrada inválido.")
        
        if len(texto_simples) > 3000:
            raise HTTPException(status_code=400, detail="Texto muito longo, reduza para 3000 caracteres.")
        
        resumo_gerado = gerar_resumo(texto_simples)
        palavras = palavras_chave_texto(texto_simples)
        
        xml_resposta = formatar_resposta_xml(resumo_gerado, palavras)
        return Response(content=xml_resposta, media_type="application/xml")
    
    except HTTPException as e:
        return Response(content=f"<erro>{e.detail}</erro>", 
                        media_type="application/xml",
                        status_code=e.status_code)
    except Exception:
        return Response(content="<erro>Erro interno no servidor.</erro>",
                        media_type="application/xml",
                        status_code=500)



@app.post("/resumir/", response_model=Resumo)
def criar_resumo(entrada: TextoEntrada):
    if not entrada.texto.strip():
        raise HTTPException(status_code=400, detail="Erro: o texto de entrada está vazio.")

    markdown_texto = entrada.texto
    texto_simples = markdown_para_texto(markdown_texto)

    if not texto_simples:
        raise HTTPException(status_code=400, detail="Erro: formato de entrada inválido.")

    if len(texto_simples) > 3000:
        raise HTTPException(status_code=400, detail="Texto muito longo, reduza para 3000 caracteres.")

    resumo_gerado = gerar_resumo(texto_simples)

    novo_resumo = Resumo(texto=resumo_gerado)
    resumos.append(novo_resumo)
    return novo_resumo

@app.get("/resumos/", response_model=List[Resumo])
def listar_resumos():
    return resumos

@app.post("/palavras-chaves/", response_model=PalavrasChave)
def palavras_chave(entrada: TextoEntrada):
    if not entrada.texto.strip():
        raise HTTPException(status_code=400, detail="Erro: texto inválido para extração de palavras-chave.")
    
    texto_simples = markdown_para_texto(entrada.texto)
    palavras = palavras_chave_texto(texto_simples)
    
    if not palavras:
        raise HTTPException(status_code=400, detail="Erro: não foi possível extrair palavras-chave do texto.")
    
    return PalavrasChave(palavras=palavras)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    error_msgs = [f"{err['msg']} ({'.'.join(map(str, err['loc']))})" for err in errors]
    return Response(
        content=f"<erro>{'; '.join(error_msgs)}</erro>",
        media_type="application/xml",
        status_code=422)
