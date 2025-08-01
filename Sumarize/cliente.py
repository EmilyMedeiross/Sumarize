import requests
#lembrar de instalar "pip install requests"

BASE_URL = "http://localhost:8000"

def criar_resumo():
    """Cria um novo resumo enviando texto para a API"""
    print("\n--- CRIAR NOVO RESUMO ---")
    texto = input("Digite o texto para resumir:\n> ")
    
    if not texto.strip():
        print("Erro: Texto não pode ser vazio!")
        return
    
    try:
        response = requests.post(
            f"{BASE_URL}/resumir/",
            json={"texto": texto}
        )
        
        if response.status_code == 200:
            resumo = response.json()
            print(f"Resumo criado com sucesso! (ID: {resumo['id']})")
            print(f"Resumo: {resumo['texto']}")
        else:
            print(f"Erro {response.status_code}: {response.text}")
    
    except Exception as e:
       print(f"Falha na comunicação com a API: {str(e)}")

def listar_resumos():
    """Lista todos os resumos cadastrados na API"""
    print("\n--- LISTA DE RESUMOS ---")
    try:
        response = requests.get(f"{BASE_URL}/resumos/")
        
        if response.status_code == 200:
            resumos = response.json()
            if not resumos:
                print("Nenhum resumo cadastrado.")
                return
                
            for resumo in resumos:
                print(f"\nID: {resumo['id']}")
                print(f"Resumo: {resumo['texto']}")
        else:
            print(f"Erro {response.status_code}: {response.text}")
    
    except Exception as e:
        print(f"Falha na comunicação com a API: {str(e)}")


        print(f"Falha na comunicação com a API: {str(e)}")

def atualizar_resumo():
    """Atualiza um resumo existente pelo ID"""
    print("\n--- ATUALIZAR RESUMO ---")
    try:
        resumo_id = int(input("Digite o ID do resumo a ser atualizado: "))
    except ValueError:
        print("ID inválido! Deve ser um número inteiro.")
        return
    
    texto = input("Digite o novo texto:\n> ")
    
    try:
        response = requests.put(
            f"{BASE_URL}/resumos/{resumo_id}",
            json={"texto": texto}
        )
        
        if response.status_code == 200:
            resumo = response.json()
            print("\n Resumo atualizado com sucesso!")
            print(f"Novo resumo: {resumo['texto']}")
        else:
            print(f"Erro {response.status_code}: {response.text}")
    
    except Exception as e:
        print(f"Falha na comunicação com a API: {str(e)}")

def deletar_resumo():
    """Exclui um resumo pelo ID"""
    print("\n--- EXCLUIR RESUMO ---")
    try:
        resumo_id = int(input("Digite o ID do resumo a ser excluído: "))
    except ValueError:
        print("ID inválido! Deve ser um número inteiro.")
        return
    
    try:
        response = requests.delete(f"{BASE_URL}/resumos/{resumo_id}")
        
        if response.status_code == 200:
            print("\n Resumo excluído com sucesso!")
        else:
            print(f"Erro {response.status_code}: {response.text}")
    
    except Exception as e:
        print(f"Falha na comunicação com a API: {str(e)}")

def extrair_palavras_chave():
    """Extrai palavras-chave de um texto sem salvar no banco"""
    print("\n--- EXTRAIR PALAVRAS-CHAVE ---")
    texto = input("Digite o texto para análise:\n> ")
    
    try:
        response = requests.post(
            f"{BASE_URL}/palavras-chaves/",
            json={"texto": texto}
        )
        
        if response.status_code == 200:
            palavras = response.json()["palavras"]
            print("\n🔑 Palavras-chave encontradas:")
            for i, palavra in enumerate(palavras, 1):
                print(f"{i}. {palavra}")
        else:
            print(f"Erro {response.status_code}: {response.text}")
    
    except Exception as e:
        print(f"Falha na comunicação com a API: {str(e)}")

def processar_texto():
    """Processa texto e retorna resultado completo em XML"""
    print("\n--- PROCESSAR TEXTO (XML) ---")
    texto = input("Digite o texto para processamento:\n> ")
    
    try:
        response = requests.post(
            f"{BASE_URL}/processar/",
            json={"texto": texto},
            headers={"Accept": "application/xml"}
        )
        
        if response.status_code == 200:
            print("\n Resposta XML:")
            print(response.text)
        else:
            print(f"Erro {response.status_code}: {response.text}")
    
    except Exception as e:
        print(f"Falha na comunicação com a API: {str(e)}")

def mostrar_menu():
    """Exibe o menu principal de opções"""
    print("\n" + "=" * 40)
    print("MENU PRINCIPAL - API DE RESUMOS")
    print("=" * 40)
    print("1. Criar novo resumo")
    print("2. Listar todos os resumos")
    print("3. Atualizar um resumo")
    print("4. Excluir um resumo")
    print("5. Extrair palavras-chave")
    print("6. Processar texto (XML)")
    print("0. Sair")
    return input("\nEscolha uma opção: ")

def main():
    """Função principal que controla o fluxo do programa"""
    while True:
        opcao = mostrar_menu()
        
        if opcao == "1":
            criar_resumo()
        elif opcao == "2":
            listar_resumos()
        elif opcao == "3":
            atualizar_resumo()
        elif opcao == "4":
            deletar_resumo()
        elif opcao == "5":
            extrair_palavras_chave()
        elif opcao == "6":
            processar_texto()
        elif opcao == "0":
            print("\nSaindo do sistema...")
            break
        else:
            print("\n Opção inválida! Tente novamente.")
            
if __name__ == "__main__":
    main()