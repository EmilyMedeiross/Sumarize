import re
from fastapi import FastAPI, HTTPException
from typing import List
from models import Resumo, TextoEntrada, PalavrasChave

app = FastAPI()

resumos: List[Resumo] = []

IGNORE_WORDS = {"o", "a", "os", "as", "um", "uma", "uns", "umas", 
             "de", "do", "da", "dos", "das", "em", "no", "na", 
        "nos", "nas", "por", "para", "com", "sem", "que", "e", "é"}


def markdown_para_texto(markdown: str) -> str:
    texto = markdown

    texto = re.sub(r'#+\s?', '', texto)

    texto = re.sub(r'(\*\*|__)(.*?)\1', r'\2', texto)
    texto = re.sub(r'(\*|_)(.*?)\1', r'\2', texto)

    texto = re.sub(r'^[-*+]\s+', '', texto, flags=re.MULTILINE)
 
    texto = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', texto)
  
    texto = re.sub(r'[`>]', '', texto)

    return texto.strip()

def gerar_resumo(texto: str) -> str:

    texto = re.sub(r'[#*_`\-]+', '', texto)

    texto = texto.replace('\n', ' ').strip()

    frases = re.split(r'(?<=[.!?])\s+', texto)

    resumo = ' '.join(frases[:3])
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

