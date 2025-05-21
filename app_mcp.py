import streamlit as st
import json
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# NOTA: Esta aplicação é um mockup da interface dos serviços MCP
# Para usar os serviços reais, é necessário instalar as bibliotecas correspondentes
# e configurar os servidores corretamente

def generate_mcp_code(service, command, params):
    """
    Gera código Python para chamar um serviço MCP.
    
    Args:
        service (str): Nome do serviço MCP ('lightrag', 'puppeteer' ou 'desktop-commander')
        command (str): Comando específico do serviço
        params (dict): Parâmetros para o comando
    
    Returns:
        str: Código Python para executar o comando MCP
    """
    code = f"""
# Código para executar {command} via MCP
import json
from claude import MCP

# Conectar ao serviço {service}
{service}_service = MCP.connect_to_service('{service}')

# Parâmetros para o comando
params = {json.dumps(params, indent=4, ensure_ascii=False)}

# Executar comando
resultado = {service}_service.{command}(**params)

# Exibir resultado
print(f"Resultado da operação {command}:")
print(json.dumps(resultado, indent=2, ensure_ascii=False))
"""
    return code

def lightrag_ui():
    """Interface de usuário para interagir com o LightRAG MCP."""
    st.header("LightRAG MCP")
    
    # Seleção do comando
    command = st.selectbox(
        "Selecione o comando:",
        ["rag_query", "rag_insert_text", "rag_insert_file"]
    )
    
    # Formulário para os parâmetros
    with st.form(key="lightrag_form"):
        params = {}
        
        if command == "rag_query":
            query = st.text_area("Consulta", help="Digite a pergunta que deseja fazer ao LightRAG.")
            mode = st.selectbox(
                "Modo de consulta",
                ["naive", "local", "global", "hybrid"],
                help="Modo de recuperação: naive (básico), local (contexto próximo), global (toda base) ou hybrid (combinado)."
            )
            only_need_context = st.checkbox("Retornar apenas o contexto", help="Se marcado, retorna apenas o contexto sem resposta gerada.")
            
            params = {
                "query": query,
                "mode": mode,
                "onlyNeedContext": only_need_context
            }
            
        elif command == "rag_insert_text":
            text = st.text_area("Texto", help="Digite o texto que deseja inserir na base de conhecimento.")
            params = {"text": text}
            
        elif command == "rag_insert_file":
            file_path = st.text_input("Caminho do arquivo", help="Caminho absoluto para o arquivo que deseja inserir.")
            params = {"file_path": file_path}
        
        # Botão para gerar o código
        submitted = st.form_submit_button("Gerar Código")
        
        if submitted:
            code = generate_mcp_code("lightrag", command, params)
            st.session_state.code = code
            st.session_state.active_mcp = "lightrag"
            st.session_state.command = command

def desktop_commander_ui():
    """Interface de usuário para interagir com o Desktop Commander MCP."""
    st.header("Desktop Commander MCP")
    
    # Seleção do comando
    command = st.selectbox(
        "Selecione o comando:",
        [
            "get_config", 
            "set_config_value",
            "read_file",
            "read_multiple_files",
            "write_file",
            "list_directory",
            "search_code",
            "create_directory",
            "search_files",
            "get_file_info",
            "move_file",
            "edit_block",
            "execute_command",
            "list_processes",
            "list_sessions",
            "kill_process",
            "force_terminate",
            "read_output"
        ]
    )
    
    # Formulário para os parâmetros específicos de cada comando
    with st.form(key="desktop_commander_form"):
        params = {}
        
        # Interface específica para cada comando
        if command == "get_config":
            # Não requer parâmetros
            st.info("Este comando não requer parâmetros.")
            params = {}
            
        elif command == "set_config_value":
            key = st.text_input("Chave", help="Chave de configuração a ser alterada.")
            value_type = st.selectbox("Tipo de valor", ["string", "number", "boolean", "array", "object"])
            
            if value_type == "string":
                value = st.text_input("Valor (string)")
            elif value_type == "number":
                value = st.number_input("Valor (number)", step=1)
            elif value_type == "boolean":
                value = st.checkbox("Valor (boolean)")
            elif value_type == "array":
                value_str = st.text_area("Valor (array JSON)", help="Ex: [\"valor1\", \"valor2\"]")
                try:
                    value = json.loads(value_str)
                except:
                    st.error("Valor JSON inválido para array")
                    value = []
            elif value_type == "object":
                value_str = st.text_area("Valor (object JSON)", help="Ex: {\"chave\": \"valor\"}")
                try:
                    value = json.loads(value_str)
                except:
                    st.error("Valor JSON inválido para objeto")
                    value = {}
            
            params = {
                "key": key,
                "value": value
            }
            
        elif command == "read_file":
            path = st.text_input("Caminho do arquivo", help="Caminho absoluto para o arquivo.")
            is_url = st.checkbox("É uma URL", value=False)
            offset = st.number_input("Offset (linha inicial)", value=0, min_value=0, help="Linha para começar a leitura.")
            length = st.number_input("Número de linhas", value=1000, min_value=1, help="Número máximo de linhas para ler.")
            
            params = {
                "path": path,
                "isUrl": is_url,
                "offset": offset,
                "length": length
            }
            
        elif command == "read_multiple_files":
            paths_str = st.text_area("Caminhos dos arquivos (um por linha)", help="Caminhos absolutos, um por linha.")
            paths = [p.strip() for p in paths_str.split("\n") if p.strip()]
            
            params = {
                "paths": paths
            }
            
        elif command == "write_file":
            path = st.text_input("Caminho do arquivo", help="Caminho absoluto para o arquivo.")
            content = st.text_area("Conteúdo", help="Conteúdo a ser escrito no arquivo.")
            mode = st.selectbox("Modo", ["rewrite", "append"], help="Modo de escrita: sobrescrever ou anexar.")
            
            params = {
                "path": path,
                "content": content,
                "mode": mode
            }
            
        elif command == "list_directory":
            path = st.text_input("Caminho do diretório", help="Caminho absoluto para o diretório.")
            
            params = {
                "path": path
            }
            
        elif command == "search_code":
            path = st.text_input("Caminho base", help="Diretório para iniciar a busca.")
            pattern = st.text_input("Padrão de busca", help="Expressão regular para buscar no conteúdo dos arquivos.")
            file_pattern = st.text_input("Padrão de arquivo (opcional)", help="Filtro para tipos de arquivo, ex: *.py")
            context_lines = st.number_input("Linhas de contexto", value=2, min_value=0, help="Número de linhas de contexto ao redor dos resultados.")
            ignore_case = st.checkbox("Ignorar maiúsculas/minúsculas", value=True)
            include_hidden = st.checkbox("Incluir arquivos ocultos", value=False)
            max_results = st.number_input("Máximo de resultados", value=100, min_value=1)
            timeout_ms = st.number_input("Timeout (ms)", value=30000, min_value=1000, help="Tempo máximo de execução em ms.")
            
            params = {
                "path": path,
                "pattern": pattern,
                "contextLines": context_lines,
                "ignoreCase": ignore_case,
                "includeHidden": include_hidden,
                "maxResults": max_results,
                "timeoutMs": timeout_ms
            }
            
            if file_pattern:
                params["filePattern"] = file_pattern
                
        elif command == "create_directory":
            path = st.text_input("Caminho do diretório", help="Caminho absoluto para o diretório a ser criado.")
            
            params = {
                "path": path
            }
            
        elif command == "search_files":
            path = st.text_input("Caminho base", help="Diretório para iniciar a busca.")
            pattern = st.text_input("Padrão de busca", help="Parte do nome do arquivo a ser buscado.")
            timeout_ms = st.number_input("Timeout (ms)", value=30000, min_value=1000, help="Tempo máximo de execução em ms.")
            
            params = {
                "path": path,
                "pattern": pattern,
                "timeoutMs": timeout_ms
            }
            
        elif command == "get_file_info":
            path = st.text_input("Caminho do arquivo", help="Caminho absoluto para o arquivo ou diretório.")
            
            params = {
                "path": path
            }
            
        elif command == "move_file":
            source = st.text_input("Origem", help="Caminho absoluto do arquivo de origem.")
            destination = st.text_input("Destino", help="Caminho absoluto de destino.")
            
            params = {
                "source": source,
                "destination": destination
            }
            
        elif command == "edit_block":
            file_path = st.text_input("Caminho do arquivo", help="Caminho absoluto para o arquivo.")
            old_string = st.text_area("Texto original", help="Texto a ser substituído (exatamente como está no arquivo).")
            new_string = st.text_area("Novo texto", help="Texto substituto.")
            expected_replacements = st.number_input("Número esperado de substituições", value=1, min_value=1, help="Número esperado de ocorrências a substituir.")
            
            params = {
                "file_path": file_path,
                "old_string": old_string,
                "new_string": new_string,
                "expected_replacements": expected_replacements
            }
            
        elif command == "execute_command":
            cmd = st.text_input("Comando", help="Comando a ser executado.")
            shell = st.text_input("Shell (opcional)", help="Shell a ser usado, padrão é bash.")
            timeout_ms = st.number_input("Timeout (ms)", value=30000, min_value=1000, help="Tempo máximo de execução em ms.")
            
            params = {
                "command": cmd,
                "timeout_ms": timeout_ms
            }
            
            if shell:
                params["shell"] = shell
                
        elif command == "list_processes":
            # Não requer parâmetros
            st.info("Este comando não requer parâmetros.")
            params = {}
            
        elif command == "list_sessions":
            # Não requer parâmetros
            st.info("Este comando não requer parâmetros.")
            params = {}
            
        elif command == "kill_process":
            pid = st.number_input("PID", value=0, min_value=0, help="ID do processo a ser terminado.")
            
            params = {
                "pid": pid
            }
            
        elif command == "force_terminate":
            pid = st.number_input("PID", value=0, min_value=0, help="ID da sessão a ser terminada.")
            
            params = {
                "pid": pid
            }
            
        elif command == "read_output":
            pid = st.number_input("PID", value=0, min_value=0, help="ID da sessão para ler a saída.")
            
            params = {
                "pid": pid
            }
        
        # Botão para gerar o código
        submitted = st.form_submit_button("Gerar Código")
        
        if submitted:
            code = generate_mcp_code("desktop-commander", command, params)
            st.session_state.code = code
            st.session_state.active_mcp = "desktop-commander"
            st.session_state.command = command

def puppeteer_ui():
    """Interface de usuário para interagir com o Puppeteer MCP."""
    st.header("Puppeteer MCP")
    
    # Seleção do comando
    command = st.selectbox(
        "Selecione o comando:",
        [
            "puppeteer_navigate", 
            "puppeteer_screenshot", 
            "puppeteer_click",
            "puppeteer_fill",
            "puppeteer_select",
            "puppeteer_hover",
            "puppeteer_evaluate"
        ]
    )
    
    # Formulário para os parâmetros
    with st.form(key="puppeteer_form"):
        params = {}
        
        if command == "puppeteer_navigate":
            url = st.text_input("URL", help="URL para navegar.")
            allow_dangerous = st.checkbox("Permitir opções perigosas", value=False, help="Se marcado, permite opções de lançamento que reduzem a segurança.")
            launch_options_str = st.text_area("Opções de lançamento (JSON)", value="{}", help="Opções de lançamento em formato JSON.")
            
            try:
                launch_options = json.loads(launch_options_str) if launch_options_str.strip() else {}
                params = {
                    "url": url,
                    "allowDangerous": allow_dangerous
                }
                if launch_options:
                    params["launchOptions"] = launch_options
            except json.JSONDecodeError:
                st.error("As opções de lançamento devem estar em formato JSON válido.")
                return
            
        elif command == "puppeteer_screenshot":
            name = st.text_input("Nome", help="Nome para o screenshot.")
            selector = st.text_input("Seletor CSS (opcional)", help="Seletor CSS para o elemento a ser capturado na screenshot.")
            width = st.number_input("Largura", value=800, help="Largura em pixels.")
            height = st.number_input("Altura", value=600, help="Altura em pixels.")
            encoded = st.checkbox("Codificar em Base64", value=False, help="Se marcado, captura a screenshot como uma URI de dados codificada em base64.")
            
            params = {
                "name": name,
                "width": width,
                "height": height,
                "encoded": encoded
            }
            if selector:
                params["selector"] = selector
                
        elif command == "puppeteer_click":
            selector = st.text_input("Seletor CSS", help="Seletor CSS para o elemento a ser clicado.")
            params = {"selector": selector}
            
        elif command == "puppeteer_fill":
            selector = st.text_input("Seletor CSS", help="Seletor CSS para o campo de entrada.")
            value = st.text_input("Valor", help="Valor a ser preenchido.")
            params = {
                "selector": selector, 
                "value": value
            }
            
        elif command == "puppeteer_select":
            selector = st.text_input("Seletor CSS", help="Seletor CSS para o elemento select.")
            value = st.text_input("Valor", help="Valor a ser selecionado.")
            params = {
                "selector": selector, 
                "value": value
            }
            
        elif command == "puppeteer_hover":
            selector = st.text_input("Seletor CSS", help="Seletor CSS para o elemento a ser hover.")
            params = {"selector": selector}
            
        elif command == "puppeteer_evaluate":
            script = st.text_area("Script JavaScript", help="Código JavaScript para executar no console do navegador.")
            params = {"script": script}
        
        # Botão para gerar o código
        submitted = st.form_submit_button("Gerar Código")
        
        if submitted:
            code = generate_mcp_code("puppeteer", command, params)
            st.session_state.code = code
            st.session_state.active_mcp = "puppeteer"
            st.session_state.command = command

def explore_entity(memory_service, entity_name):
    """Interface interativa para explorar uma entidade específica."""
    try:
        # Buscar a entidade específica
        result = memory_service.open_nodes({"names": [entity_name]})
        if not result or not result.get("entities"):
            st.error(f"Entidade '{entity_name}' não encontrada.")
            return
        
        entity = next((e for e in result["entities"] if e["name"] == entity_name), None)
        if not entity:
            st.error(f"Entidade '{entity_name}' não encontrada.")
            return
        
        # Exibir informações detalhadas da entidade
        st.subheader(f"Detalhes de: {entity['name']}")
        st.write(f"**Tipo:** {entity['entityType']}")
        
        # Observações com possibilidade de editar/excluir
        st.write("**Observações:**")
        for i, obs in enumerate(entity["observations"]):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.text(obs)
            with col2:
                if st.button("Remover", key=f"del_obs_{entity_name}_{i}"):
                    try:
                        memory_service.delete_observations({
                            "deletions": [{
                                "entityName": entity_name,
                                "observations": [obs]
                            }]
                        })
                        st.success("Observação removida!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Erro ao remover observação: {str(e)}")
        
        # Adicionar nova observação
        with st.expander("Adicionar nova observação"):
            new_obs = st.text_area("Nova observação", key=f"new_obs_{entity_name}")
            if st.button("Adicionar", key=f"add_obs_{entity_name}"):
                if new_obs.strip():
                    try:
                        memory_service.add_observations({
                            "observations": [{
                                "entityName": entity_name,
                                "contents": [new_obs]
                            }]
                        })
                        st.success("Observação adicionada!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Erro ao adicionar observação: {str(e)}")
        
        # Mostrar relações onde esta entidade participa
        st.subheader("Relações")
        
        # Buscar o grafo completo para encontrar relações
        full_graph = memory_service.read_graph()
        
        # Relações onde a entidade é origem
        outgoing = [r for r in full_graph.get("relations", []) if r["from"] == entity_name]
        if outgoing:
            st.write("**Relações de saída:**")
            for i, rel in enumerate(outgoing):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"→ **{rel['relationType']}** → {rel['to']}")
                with col2:
                    if st.button("X", key=f"del_out_rel_{i}"):
                        try:
                            memory_service.delete_relations({
                                "relations": [{
                                    "from": rel["from"],
                                    "relationType": rel["relationType"],
                                    "to": rel["to"]
                                }]
                            })
                            st.success("Relação removida!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Erro ao remover relação: {str(e)}")
        else:
            st.info("Não há relações de saída.")
        
        # Relações onde a entidade é destino
        incoming = [r for r in full_graph.get("relations", []) if r["to"] == entity_name]
        if incoming:
            st.write("**Relações de entrada:**")
            for i, rel in enumerate(incoming):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"{rel['from']} → **{rel['relationType']}** →")
                with col2:
                    if st.button("X", key=f"del_in_rel_{i}"):
                        try:
                            memory_service.delete_relations({
                                "relations": [{
                                    "from": rel["from"],
                                    "relationType": rel["relationType"],
                                    "to": rel["to"]
                                }]
                            })
                            st.success("Relação removida!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Erro ao remover relação: {str(e)}")
        else:
            st.info("Não há relações de entrada.")
        
        # Adicionar nova relação
        with st.expander("Adicionar nova relação"):
            # Opções para criar novas relações
            rel_direction = st.radio("Direção da relação", ["De esta entidade para outra", "De outra entidade para esta"])
            
            # Lista de outras entidades disponíveis
            other_entities = [e["name"] for e in full_graph.get("entities", []) if e["name"] != entity_name]
            
            if rel_direction == "De esta entidade para outra":
                # Esta entidade como origem
                if other_entities:
                    to_entity = st.selectbox("Entidade de destino", other_entities)
                    rel_type = st.text_input("Tipo de relação")
                    
                    if st.button("Criar relação") and rel_type.strip():
                        try:
                            memory_service.create_relations({
                                "relations": [{
                                    "from": entity_name,
                                    "relationType": rel_type,
                                    "to": to_entity
                                }]
                            })
                            st.success("Relação criada!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Erro ao criar relação: {str(e)}")
                else:
                    st.info("Não há outras entidades disponíveis para criar relações.")
            else:
                # Esta entidade como destino
                if other_entities:
                    from_entity = st.selectbox("Entidade de origem", other_entities)
                    rel_type = st.text_input("Tipo de relação")
                    
                    if st.button("Criar relação") and rel_type.strip():
                        try:
                            memory_service.create_relations({
                                "relations": [{
                                    "from": from_entity,
                                    "relationType": rel_type,
                                    "to": entity_name
                                }]
                            })
                            st.success("Relação criada!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Erro ao criar relação: {str(e)}")
                else:
                    st.info("Não há outras entidades disponíveis para criar relações.")
                
    except Exception as e:
        st.error(f"Erro ao explorar entidade: {str(e)}")

def view_graph_direct(memory_service):
    """Mostra diretamente o conteúdo do grafo sem necessidade de formulários."""
    try:
        # Buscar o grafo
        current_graph = memory_service.read_graph()
        
        # Exibir o resultado em formato de tabela ou JSON
        st.subheader("Grafo de Conhecimento Memory MCP")
        
        # Contadores
        entidades_count = len(current_graph.get("entities", []))
        relacoes_count = len(current_graph.get("relations", []))
        
        # Mostrar estatísticas
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Entidades", entidades_count)
        with col2:
            st.metric("Relações", relacoes_count)
        
        # Entidades
        if current_graph.get("entities"):
            st.subheader("Entidades")
            
            # Criar tabela de entidades
            entities_data = []
            for entity in current_graph["entities"]:
                obs_preview = ""
                if entity["observations"]:
                    obs_preview = entity["observations"][0][:100]
                    if len(entity["observations"][0]) > 100:
                        obs_preview += "..."
                
                entities_data.append({
                    "Nome": entity["name"],
                    "Tipo": entity["entityType"],
                    "Observações": len(entity["observations"]),
                    "Prévia": obs_preview
                })
            
            if entities_data:
                st.dataframe(entities_data, use_container_width=True)
        else:
            st.info("Não foram encontradas entidades no grafo.")
        
        # Relações
        if current_graph.get("relations"):
            st.subheader("Relações")
            
            # Criar tabela de relações
            relations_data = []
            for relation in current_graph["relations"]:
                relations_data.append({
                    "De": relation["from"],
                    "Relação": relation["relationType"],
                    "Para": relation["to"]
                })
            
            if relations_data:
                st.dataframe(relations_data, use_container_width=True)
        else:
            st.info("Não foram encontradas relações no grafo.")
        
        # Opção para visualizar o JSON completo
        with st.expander("Ver JSON completo"):
            st.json(current_graph)
            
        # Opção para explorar uma entidade específica
        if entidades_count > 0:
            st.subheader("Explorar Entidade Específica")
            entity_names = [e["name"] for e in current_graph.get("entities", [])]
            selected_entity = st.selectbox("Selecione uma entidade:", [""] + entity_names)
            
            if selected_entity:
                st.session_state.selected_entity = selected_entity
                st.session_state.memory_view = "entity"
                st.experimental_rerun()
    
    except Exception as e:
        st.error(f"Erro ao ler o grafo: {str(e)}")

def memory_ui():
    """Interface de usuário para interagir com o Memory MCP."""
    st.header("Memory MCP")
    
    # Inicializar estado da sessão para Memory
    if "memory_view" not in st.session_state:
        st.session_state.memory_view = "graph"  # opções: "graph", "entity", "search"
    if "selected_entity" not in st.session_state:
        st.session_state.selected_entity = None
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    if "direct_view" not in st.session_state:
        st.session_state.direct_view = False  # Para mostrar diretamente o grafo
    
    # Mostrar o estado atual do grafo
    try:
        from claude import MCP
        memory_service = MCP.connect_to_service('memory')
        
        # Barra de navegação para o Memory
        tabs = ["Grafo", "Pesquisar", "Comandos", "Visualização Direta"]
        selected_tab = st.radio("Navegação:", tabs, horizontal=True)
        
        if selected_tab == "Grafo":
            st.session_state.memory_view = "graph"
            st.session_state.direct_view = False
        elif selected_tab == "Pesquisar":
            st.session_state.memory_view = "search"
            st.session_state.direct_view = False
        elif selected_tab == "Comandos":
            st.session_state.memory_view = "commands"
            st.session_state.direct_view = False
        elif selected_tab == "Visualização Direta":
            st.session_state.direct_view = True
            # Mostrar o grafo diretamente
            view_graph_direct(memory_service)
            return
        
        # Visualização específica da entidade
        if st.session_state.memory_view == "entity" and st.session_state.selected_entity:
            if st.button("← Voltar ao grafo"):
                st.session_state.memory_view = "graph"
                st.experimental_rerun()
            else:
                explore_entity(memory_service, st.session_state.selected_entity)
            return
        
        # Visualização de pesquisa
        elif st.session_state.memory_view == "search":
            st.subheader("Pesquisar no Grafo de Conhecimento")
            search_query = st.text_input("Termo de busca:", value=st.session_state.search_query)
            
            if st.button("Buscar") or search_query != st.session_state.search_query:
                st.session_state.search_query = search_query
                if search_query.strip():
                    try:
                        search_results = memory_service.search_nodes({"query": search_query})
                        
                        if search_results and search_results.get("entities"):
                            st.success(f"Encontrados {len(search_results['entities'])} resultados.")
                            
                            # Exibir resultados da pesquisa
                            for i, entity in enumerate(search_results["entities"]):
                                with st.container():
                                    col1, col2 = st.columns([5, 1])
                                    with col1:
                                        st.write(f"**{entity['name']}** ({entity['entityType']})")
                                        if entity.get("observations"):
                                            obs_preview = entity["observations"][0][:100]
                                            if len(entity["observations"][0]) > 100:
                                                obs_preview += "..."
                                            st.write(obs_preview)
                                    with col2:
                                        if st.button("Ver", key=f"view_search_{i}"):
                                            st.session_state.selected_entity = entity['name']
                                            st.session_state.memory_view = "entity"
                                            st.experimental_rerun()
                                
                                if i < len(search_results["entities"]) - 1:
                                    st.markdown("---")
                        else:
                            st.info(f"Nenhum resultado encontrado para '{search_query}'.")
                    except Exception as e:
                        st.error(f"Erro na pesquisa: {str(e)}")
            return
            
        # Visualização de comandos (formulários originais)
        elif st.session_state.memory_view == "commands":
            st.subheader("Comandos do Memory MCP")
            
            # Seleção do comando
            command = st.selectbox(
                "Selecione o comando:",
                [
                    "create_entities", 
                    "create_relations", 
                    "add_observations",
                    "delete_entities",
                    "delete_observations",
                    "delete_relations",
                    "read_graph",
                    "search_nodes",
                    "open_nodes"
                ]
            )
            
            # Formulário para os parâmetros
            with st.form(key="memory_form"):
                params = {}
                
                if command == "create_entities":
                    st.subheader("Criar Entidades")
                    
                    # Interface para adicionar múltiplas entidades
                    num_entities = st.number_input("Número de entidades a criar", min_value=1, value=1)
                    entities = []
                    
                    for i in range(num_entities):
                        st.markdown(f"#### Entidade {i+1}")
                        name = st.text_input(f"Nome da entidade {i+1}", key=f"entity_name_{i}")
                        entity_type = st.text_input(f"Tipo da entidade {i+1}", key=f"entity_type_{i}")
                        observations_text = st.text_area(f"Observações (uma por linha) para entidade {i+1}", key=f"entity_obs_{i}")
                        observations = [obs.strip() for obs in observations_text.split("\n") if obs.strip()]
                        
                        if name and entity_type and observations:
                            entities.append({
                                "name": name,
                                "entityType": entity_type,
                                "observations": observations
                            })
                    
                    params = {"entities": entities}
                    
                elif command == "create_relations":
                    st.subheader("Criar Relações")
                    
                    # Interface para adicionar múltiplas relações
                    num_relations = st.number_input("Número de relações a criar", min_value=1, value=1)
                    relations = []
                    
                    for i in range(num_relations):
                        st.markdown(f"#### Relação {i+1}")
                        from_entity = st.text_input(f"Entidade de origem {i+1}", key=f"from_{i}")
                        relation_type = st.text_input(f"Tipo de relação {i+1}", key=f"relation_type_{i}")
                        to_entity = st.text_input(f"Entidade de destino {i+1}", key=f"to_{i}")
                        
                        if from_entity and relation_type and to_entity:
                            relations.append({
                                "from": from_entity,
                                "relationType": relation_type,
                                "to": to_entity
                            })
                    
                    params = {"relations": relations}
                    
                elif command == "add_observations":
                    st.subheader("Adicionar Observações")
                    
                    # Interface para adicionar observações a entidades existentes
                    num_entities = st.number_input("Número de entidades para adicionar observações", min_value=1, value=1)
                    observations = []
                    
                    for i in range(num_entities):
                        st.markdown(f"#### Observações para Entidade {i+1}")
                        entity_name = st.text_input(f"Nome da entidade {i+1}", key=f"obs_entity_{i}")
                        contents_text = st.text_area(f"Observações (uma por linha) para a entidade {i+1}", key=f"obs_contents_{i}")
                        contents = [content.strip() for content in contents_text.split("\n") if content.strip()]
                        
                        if entity_name and contents:
                            observations.append({
                                "entityName": entity_name,
                                "contents": contents
                            })
                    
                    params = {"observations": observations}
                    
                elif command == "delete_entities":
                    st.subheader("Excluir Entidades")
                    
                    entity_names_text = st.text_area("Nomes das entidades (uma por linha)")
                    entity_names = [name.strip() for name in entity_names_text.split("\n") if name.strip()]
                    
                    params = {"entityNames": entity_names}
                    
                elif command == "delete_observations":
                    st.subheader("Excluir Observações")
                    
                    # Interface para excluir observações de entidades
                    num_entities = st.number_input("Número de entidades para excluir observações", min_value=1, value=1)
                    deletions = []
                    
                    for i in range(num_entities):
                        st.markdown(f"#### Observações para Excluir da Entidade {i+1}")
                        entity_name = st.text_input(f"Nome da entidade {i+1}", key=f"del_ent_{i}")
                        observations_text = st.text_area(f"Observações a excluir (uma por linha) da entidade {i+1}", key=f"del_obs_{i}")
                        observations = [obs.strip() for obs in observations_text.split("\n") if obs.strip()]
                        
                        if entity_name and observations:
                            deletions.append({
                                "entityName": entity_name,
                                "observations": observations
                            })
                    
                    params = {"deletions": deletions}
                    
                elif command == "delete_relations":
                    st.subheader("Excluir Relações")
                    
                    # Interface para excluir relações
                    num_relations = st.number_input("Número de relações a excluir", min_value=1, value=1)
                    relations = []
                    
                    for i in range(num_relations):
                        st.markdown(f"#### Relação {i+1} para Excluir")
                        from_entity = st.text_input(f"Entidade de origem {i+1}", key=f"del_from_{i}")
                        relation_type = st.text_input(f"Tipo de relação {i+1}", key=f"del_rel_type_{i}")
                        to_entity = st.text_input(f"Entidade de destino {i+1}", key=f"del_to_{i}")
                        
                        if from_entity and relation_type and to_entity:
                            relations.append({
                                "from": from_entity,
                                "relationType": relation_type,
                                "to": to_entity
                            })
                    
                    params = {"relations": relations}
                    
                elif command == "read_graph":
                    st.info("Este comando não requer parâmetros e mostra automaticamente o conteúdo do grafo.")
                    params = {}
                    
                    # Mostrar o conteúdo diretamente sem precisar gerar código
                    st.markdown("---")
                    st.markdown("### Visualização Automática do Grafo")
                    st.info("Os resultados são mostrados automaticamente abaixo:")
                    
                    # Usar a função existente para mostrar o grafo
                    view_graph_direct(memory_service)
                    
                    # Adicionar botão para abrir em visualização completa
                    if st.button("Abrir em Visualização Completa"):
                        st.session_state.direct_view = True
                        st.experimental_rerun()
                    
                elif command == "search_nodes":
                    query = st.text_input("Consulta de busca", help="Texto para buscar nomes, tipos ou conteúdo de observações de entidades.")
                    params = {"query": query}
                    
                    # Executar busca quando houver um termo de busca
                    if query.strip():
                        try:
                            # Executar a busca
                            search_results = memory_service.search_nodes({"query": query})
                            
                            # Exibir resultados
                            st.subheader("Resultados da busca:")
                            
                            if search_results and search_results.get("entities"):
                                entities = search_results["entities"]
                                st.success(f"Encontradas {len(entities)} entidades para '{query}'")
                                
                                # Criar tabela com resultados
                                results_data = []
                                for entity in entities:
                                    obs_preview = ""
                                    if entity.get("observations") and entity["observations"]:
                                        obs_preview = entity["observations"][0][:100]
                                        if len(entity["observations"][0]) > 100:
                                            obs_preview += "..."
                                    
                                    results_data.append({
                                        "Nome": entity["name"],
                                        "Tipo": entity["entityType"],
                                        "Prévia": obs_preview
                                    })
                                
                                st.table(results_data)
                                
                                # Ver detalhes de uma entidade específica
                                select_entity = st.selectbox("Visualizar detalhes de:", 
                                                           ["Selecione uma entidade..."] + [e["name"] for e in entities])
                                
                                if select_entity != "Selecione uma entidade...":
                                    # Encontrar a entidade selecionada nos resultados
                                    selected = next((e for e in entities if e["name"] == select_entity), None)
                                    if selected:
                                        with st.expander(f"Detalhes de {select_entity}", expanded=True):
                                            st.write(f"**Nome:** {selected['name']}")
                                            st.write(f"**Tipo:** {selected['entityType']}")
                                            st.write("**Observações:**")
                                            for obs in selected.get("observations", []):
                                                st.text(obs)
                            else:
                                st.info(f"Nenhum resultado encontrado para '{query}'")
                        
                        except Exception as e:
                            st.error(f"Erro na busca: {str(e)}")
                    
                elif command == "open_nodes":
                    names_text = st.text_area("Nomes das entidades (uma por linha)")
                    names = [name.strip() for name in names_text.split("\n") if name.strip()]
                    params = {"names": names}
                    
                    # Executar a abertura de nós quando houver nomes
                    if names:
                        try:
                            # Executar a busca por nomes específicos
                            result = memory_service.open_nodes({"names": names})
                            
                            # Exibir resultados
                            st.subheader("Entidades encontradas:")
                            
                            if result and result.get("entities"):
                                entities = result["entities"]
                                st.success(f"Encontradas {len(entities)} entidades")
                                
                                # Exibir cada entidade em um card expansível
                                for i, entity in enumerate(entities):
                                    with st.expander(f"{entity['name']} ({entity['entityType']})", expanded=True):
                                        st.write(f"**Nome:** {entity['name']}")
                                        st.write(f"**Tipo:** {entity['entityType']}")
                                        
                                        # Observações
                                        st.write("**Observações:**")
                                        if entity.get("observations"):
                                            for obs in entity["observations"]:
                                                st.text(obs)
                                        else:
                                            st.info("Sem observações")
                                        
                                        # Obter relações para esta entidade (requer consulta ao grafo completo)
                                        try:
                                            full_graph = memory_service.read_graph()
                                            
                                            # Relações de saída
                                            outgoing = [r for r in full_graph.get("relations", []) if r["from"] == entity["name"]]
                                            if outgoing:
                                                st.write("**Relações de saída:**")
                                                for rel in outgoing:
                                                    st.write(f"→ **{rel['relationType']}** → {rel['to']}")
                                            
                                            # Relações de entrada
                                            incoming = [r for r in full_graph.get("relations", []) if r["to"] == entity["name"]]
                                            if incoming:
                                                st.write("**Relações de entrada:**")
                                                for rel in incoming:
                                                    st.write(f"{rel['from']} → **{rel['relationType']}** →")
                                        
                                        except Exception as e:
                                            st.warning(f"Não foi possível carregar as relações: {str(e)}")
                            else:
                                not_found = ", ".join(names)
                                st.warning(f"Nenhuma entidade encontrada com os nomes: {not_found}")
                        
                        except Exception as e:
                            st.error(f"Erro ao abrir entidades: {str(e)}")
                
                # Botão para gerar o código
                submitted = st.form_submit_button("Gerar Código")
                
                if submitted:
                    code = generate_mcp_code("memory", command, params)
                    st.session_state.code = code
                    st.session_state.active_mcp = "memory"
                    st.session_state.command = command
        
        # Visualização padrão do grafo
        else:
            graph = memory_service.read_graph()
            
            # Visualização principal do grafo
            st.subheader("Entidades no Grafo de Conhecimento")
            
            # Adicionar uma nova entidade diretamente
            with st.expander("Adicionar Nova Entidade", expanded=False):
                with st.form("add_entity_form"):
                    entity_name = st.text_input("Nome da Entidade")
                    entity_type = st.text_input("Tipo da Entidade")
                    entity_obs = st.text_area("Observações (uma por linha)")
                    
                    submitted = st.form_submit_button("Criar Entidade")
                    
                    if submitted and entity_name and entity_type and entity_obs:
                        try:
                            observations = [obs.strip() for obs in entity_obs.split("\n") if obs.strip()]
                            if observations:
                                memory_service.create_entities({
                                    "entities": [{
                                        "name": entity_name,
                                        "entityType": entity_type,
                                        "observations": observations
                                    }]
                                })
                                st.success(f"Entidade '{entity_name}' criada com sucesso!")
                                st.experimental_rerun()
                            else:
                                st.error("É necessário adicionar pelo menos uma observação.")
                        except Exception as e:
                            st.error(f"Erro ao criar entidade: {str(e)}")
            
            # Mostrar entidades em forma de cards
            if graph["entities"]:
                # Organizar em grid de cards
                num_entities = len(graph["entities"])
                cols_per_row = 2
                num_rows = (num_entities + cols_per_row - 1) // cols_per_row  # Arredondamento para cima
                
                for row in range(num_rows):
                    cols = st.columns(cols_per_row)
                    for col in range(cols_per_row):
                        idx = row * cols_per_row + col
                        if idx < num_entities:
                            entity = graph["entities"][idx]
                            with cols[col]:
                                with st.container(border=True):
                                    st.subheader(entity["name"])
                                    st.caption(f"Tipo: {entity['entityType']}")
                                    
                                    # Mostrar primeira observação
                                    if entity["observations"]:
                                        st.write(entity["observations"][0][:150] + ("..." if len(entity["observations"][0]) > 150 else ""))
                                        if len(entity["observations"]) > 1:
                                            st.caption(f"+{len(entity['observations'])-1} mais observações")
                                    
                                    # Contar relações para esta entidade
                                    outgoing = sum(1 for r in graph.get("relations", []) if r["from"] == entity["name"])
                                    incoming = sum(1 for r in graph.get("relations", []) if r["to"] == entity["name"])
                                    
                                    # Barra de ações
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        if st.button("Explorar", key=f"explore_{idx}"):
                                            st.session_state.selected_entity = entity["name"]
                                            st.session_state.memory_view = "entity"
                                            st.experimental_rerun()
                                    with col2:
                                        st.caption(f"{outgoing + incoming} relações")
                                    with col3:
                                        if st.button("Deletar", key=f"del_entity_{idx}"):
                                            try:
                                                # Deletar a entidade
                                                memory_service.delete_entities({
                                                    "entityNames": [entity["name"]]
                                                })
                                                st.success(f"Entidade '{entity['name']}' excluída!")
                                                st.experimental_rerun()
                                            except Exception as e:
                                                st.error(f"Erro: {str(e)}")
            else:
                st.info("Não há entidades no grafo atualmente.")
                st.write("Para começar, adicione uma entidade usando o painel 'Adicionar Nova Entidade' acima.")
            
            # Visualização das relações
            if graph["relations"]:
                st.subheader("Relações")
                with st.expander("Ver todas as relações", expanded=False):
                    # Dividir em colunas para layout
                    for i, relation in enumerate(graph["relations"]):
                        with st.container():
                            col1, col2 = st.columns([5, 1])
                            with col1:
                                from_part = f"**{relation['from']}**"
                                to_part = f"**{relation['to']}**"
                                st.write(f"{from_part} → **{relation['relationType']}** → {to_part}")
                            
                            with col2:
                                if st.button("X", key=f"del_relation_{i}"):
                                    try:
                                        # Deletar a relação
                                        memory_service.delete_relations({
                                            "relations": [{
                                                "from": relation["from"],
                                                "relationType": relation["relationType"],
                                                "to": relation["to"]
                                            }]
                                        })
                                        st.success(f"Relação excluída com sucesso!")
                                        st.experimental_rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao excluir relação: {str(e)}")
                        
                        # Separador entre relações
                        if i < len(graph["relations"]) - 1:
                            st.markdown("---")
                
                # Adicionar nova relação
                with st.expander("Criar Nova Relação", expanded=False):
                    if len(graph["entities"]) >= 2:
                        with st.form("add_relation_form"):
                            entity_names = [e["name"] for e in graph["entities"]]
                            from_entity = st.selectbox("De (origem)", entity_names, key="from_entity_select")
                            relation_type = st.text_input("Tipo de Relação")
                            to_entity = st.selectbox("Para (destino)", entity_names, key="to_entity_select")
                            
                            submitted = st.form_submit_button("Criar Relação")
                            
                            if submitted and from_entity and relation_type and to_entity:
                                if from_entity != to_entity:
                                    try:
                                        memory_service.create_relations({
                                            "relations": [{
                                                "from": from_entity,
                                                "relationType": relation_type,
                                                "to": to_entity
                                            }]
                                        })
                                        st.success("Relação criada com sucesso!")
                                        st.experimental_rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao criar relação: {str(e)}")
                                else:
                                    st.error("A origem e o destino não podem ser a mesma entidade.")
                    else:
                        st.info("É necessário ter pelo menos duas entidades para criar uma relação.")
            
            # Botão para limpar todo o grafo (na parte inferior da página)
            if graph["entities"] or graph["relations"]:
                st.markdown("---")
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("Limpar Grafo", type="primary"):
                        st.session_state.show_delete_warning = True
                
                # Mostrar aviso de confirmação
                if st.session_state.get("show_delete_warning", False):
                    st.warning("⚠️ Tem certeza que deseja excluir todas as entidades e relações?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Sim, excluir tudo", type="primary"):
                            try:
                                # Excluir todas as entidades (as relações serão excluídas automaticamente)
                                entity_names = [entity["name"] for entity in graph["entities"]]
                                if entity_names:
                                    memory_service.delete_entities({
                                        "entityNames": entity_names
                                    })
                                    st.success("Grafo de conhecimento limpo com sucesso!")
                                    st.session_state.show_delete_warning = False
                                    st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Erro ao limpar o grafo: {str(e)}")
                    with col2:
                        if st.button("Cancelar"):
                            st.session_state.show_delete_warning = False
                            st.experimental_rerun()
    except Exception as e:
        st.warning(f"Não foi possível conectar ao Memory MCP: {str(e)}")
        st.info("Esta aplicação é um mockup. Para usar o Memory MCP real, configure a conexão apropriadamente.")
    
    # Seleção do comando
    command = st.selectbox(
        "Selecione o comando:",
        [
            "create_entities", 
            "create_relations", 
            "add_observations",
            "delete_entities",
            "delete_observations",
            "delete_relations",
            "read_graph",
            "search_nodes",
            "open_nodes"
        ]
    )
    
    # Formulário para os parâmetros
    with st.form(key="memory_form"):
        params = {}
        
        if command == "create_entities":
            st.subheader("Criar Entidades")
            
            # Interface para adicionar múltiplas entidades
            num_entities = st.number_input("Número de entidades a criar", min_value=1, value=1)
            entities = []
            
            for i in range(num_entities):
                st.markdown(f"#### Entidade {i+1}")
                name = st.text_input(f"Nome da entidade {i+1}", key=f"entity_name_{i}")
                entity_type = st.text_input(f"Tipo da entidade {i+1}", key=f"entity_type_{i}")
                observations_text = st.text_area(f"Observações (uma por linha) para entidade {i+1}", key=f"entity_obs_{i}")
                observations = [obs.strip() for obs in observations_text.split("\n") if obs.strip()]
                
                if name and entity_type and observations:
                    entities.append({
                        "name": name,
                        "entityType": entity_type,
                        "observations": observations
                    })
            
            params = {"entities": entities}
            
        elif command == "create_relations":
            st.subheader("Criar Relações")
            
            # Interface para adicionar múltiplas relações
            num_relations = st.number_input("Número de relações a criar", min_value=1, value=1)
            relations = []
            
            for i in range(num_relations):
                st.markdown(f"#### Relação {i+1}")
                from_entity = st.text_input(f"Entidade de origem {i+1}", key=f"from_{i}")
                relation_type = st.text_input(f"Tipo de relação {i+1}", key=f"relation_type_{i}")
                to_entity = st.text_input(f"Entidade de destino {i+1}", key=f"to_{i}")
                
                if from_entity and relation_type and to_entity:
                    relations.append({
                        "from": from_entity,
                        "relationType": relation_type,
                        "to": to_entity
                    })
            
            params = {"relations": relations}
            
        elif command == "add_observations":
            st.subheader("Adicionar Observações")
            
            # Interface para adicionar observações a entidades existentes
            num_entities = st.number_input("Número de entidades para adicionar observações", min_value=1, value=1)
            observations = []
            
            for i in range(num_entities):
                st.markdown(f"#### Observações para Entidade {i+1}")
                entity_name = st.text_input(f"Nome da entidade {i+1}", key=f"obs_entity_{i}")
                contents_text = st.text_area(f"Observações (uma por linha) para a entidade {i+1}", key=f"obs_contents_{i}")
                contents = [content.strip() for content in contents_text.split("\n") if content.strip()]
                
                if entity_name and contents:
                    observations.append({
                        "entityName": entity_name,
                        "contents": contents
                    })
            
            params = {"observations": observations}
            
        elif command == "delete_entities":
            st.subheader("Excluir Entidades")
            
            entity_names_text = st.text_area("Nomes das entidades (uma por linha)")
            entity_names = [name.strip() for name in entity_names_text.split("\n") if name.strip()]
            
            params = {"entityNames": entity_names}
            
        elif command == "delete_observations":
            st.subheader("Excluir Observações")
            
            # Interface para excluir observações de entidades
            num_entities = st.number_input("Número de entidades para excluir observações", min_value=1, value=1)
            deletions = []
            
            for i in range(num_entities):
                st.markdown(f"#### Observações para Excluir da Entidade {i+1}")
                entity_name = st.text_input(f"Nome da entidade {i+1}", key=f"del_ent_{i}")
                observations_text = st.text_area(f"Observações a excluir (uma por linha) da entidade {i+1}", key=f"del_obs_{i}")
                observations = [obs.strip() for obs in observations_text.split("\n") if obs.strip()]
                
                if entity_name and observations:
                    deletions.append({
                        "entityName": entity_name,
                        "observations": observations
                    })
            
            params = {"deletions": deletions}
            
        elif command == "delete_relations":
            st.subheader("Excluir Relações")
            
            # Interface para excluir relações
            num_relations = st.number_input("Número de relações a excluir", min_value=1, value=1)
            relations = []
            
            for i in range(num_relations):
                st.markdown(f"#### Relação {i+1} para Excluir")
                from_entity = st.text_input(f"Entidade de origem {i+1}", key=f"del_from_{i}")
                relation_type = st.text_input(f"Tipo de relação {i+1}", key=f"del_rel_type_{i}")
                to_entity = st.text_input(f"Entidade de destino {i+1}", key=f"del_to_{i}")
                
                if from_entity and relation_type and to_entity:
                    relations.append({
                        "from": from_entity,
                        "relationType": relation_type,
                        "to": to_entity
                    })
            
            params = {"relations": relations}
            
        elif command == "read_graph":
            st.info("Este comando não requer parâmetros.")
            params = {}
            
        elif command == "search_nodes":
            query = st.text_input("Consulta de busca", help="Texto para buscar nomes, tipos ou conteúdo de observações de entidades.")
            params = {"query": query}
            
        elif command == "open_nodes":
            names_text = st.text_area("Nomes das entidades (uma por linha)")
            names = [name.strip() for name in names_text.split("\n") if name.strip()]
            params = {"names": names}
        
        # Botão para gerar o código
        submitted = st.form_submit_button("Gerar Código")
        
        if submitted:
            code = generate_mcp_code("memory", command, params)
            st.session_state.code = code
            st.session_state.active_mcp = "memory"
            st.session_state.command = command

def main():
    """Função principal da aplicação."""
    st.set_page_config(
        page_title="Interface MCP (Model Context Protocol)",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("Interface MCP (Model Context Protocol)")
    
    # Inicialização do estado da sessão
    if "code" not in st.session_state:
        st.session_state.code = ""
    if "active_mcp" not in st.session_state:
        st.session_state.active_mcp = None
    if "command" not in st.session_state:
        st.session_state.command = None
    
    # Sidebar com seleção de serviço MCP
    st.sidebar.title("Serviços MCP")
    service = st.sidebar.radio(
        "Selecione um serviço:",
        ["LightRAG", "Puppeteer", "Desktop Commander", "Memory"]
    )
    
    # Exibir a interface para o serviço selecionado
    if service == "LightRAG":
        lightrag_ui()
    elif service == "Puppeteer":
        puppeteer_ui()
    elif service == "Memory":
        memory_ui()
    else:
        desktop_commander_ui()
    
    # Exibir o código gerado
    if st.session_state.code:
        st.subheader(f"Código para executar {st.session_state.command}")
        st.code(st.session_state.code, language="python")
        
        if st.button("Copiar para Clipboard"):
            st.toast("Código copiado para o clipboard!", icon="✂️")
        
        if st.button("Executar"):
            st.warning("⚠️ Esta funcionalidade ainda não está implementada. O código seria executado aqui.")

if __name__ == "__main__":
    main()