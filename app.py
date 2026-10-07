import customtkinter as ctk
from pathlib import Path
import sorteio 

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class FilmesGlobalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🎬 Filmes Global")
        self.geometry("850x550")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==========================================
        # MENU LATERAL
        # ==========================================
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="🎬 Filmes\nGlobal", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_inicio = ctk.CTkButton(self.sidebar_frame, text="🏠 Início", command=self.mostrar_inicio)
        self.btn_inicio.grid(row=1, column=0, padx=20, pady=10)

        self.btn_sorteio = ctk.CTkButton(self.sidebar_frame, text="🎲 Novo Sorteio", command=self.mostrar_sorteio)
        self.btn_sorteio.grid(row=2, column=0, padx=20, pady=10)

        self.btn_historico = ctk.CTkButton(self.sidebar_frame, text="📜 Histórico", command=self.mostrar_historico)
        self.btn_historico.grid(row=3, column=0, padx=20, pady=10)

        self.switch_modo = ctk.CTkSwitch(self.sidebar_frame, text="Modo Escuro", command=self.alternar_modo)
        self.switch_modo.grid(row=5, column=0, padx=20, pady=10, sticky="s")
        if ctk.get_appearance_mode() == "Dark":
            self.switch_modo.select()

        self.btn_sair = ctk.CTkButton(self.sidebar_frame, text="Sair", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.destroy)
        self.btn_sair.grid(row=6, column=0, padx=20, pady=20)

        # ==========================================
        # TELA 1: INÍCIO
        # ==========================================
        self.frame_inicio = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        self.label_inicio = ctk.CTkLabel(self.frame_inicio, text="Bem-vindo ao Filmes Global!", font=ctk.CTkFont(size=28, weight="bold"))
        self.label_inicio.pack(pady=(50, 10))

        texto_apresentacao = (
            "Explore o cinema mundial, um país de cada vez.\n\n"
            "O Filmes Global utiliza a base de dados oficial do IMDb para te ajudar\n"
            "a descobrir obras-primas fora do circuito comercial padrão.\n"
            "Escolha um país e deixe o algoritmo encontrar o filme perfeito\n"
            "para a sua próxima sessão."
        )
        self.label_sub_inicio = ctk.CTkLabel(self.frame_inicio, text=texto_apresentacao, font=ctk.CTkFont(size=15), justify="center")
        self.label_sub_inicio.pack(pady=(10, 20))

        # ==========================================
        # TELA 2: HISTÓRICO (AGORA COM ABAS!)
        # ==========================================
        self.frame_historico = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.label_historico = ctk.CTkLabel(self.frame_historico, text="📜 Histórico de Sorteios", font=ctk.CTkFont(size=28, weight="bold"))
        self.label_historico.pack(pady=(20, 5))

        # Cria as Abas
        self.abas_historico = ctk.CTkTabview(self.frame_historico)
        self.abas_historico.pack(pady=10, padx=20, fill="both", expand=True)

        self.aba_todos = self.abas_historico.add("Todos")
        self.aba_melhores = self.abas_historico.add("Melhores Filmes")
        self.aba_aleatorios = self.abas_historico.add("Aleatórios (País)")
        self.aba_globais = self.abas_historico.add("Globais")

        # Cria uma área de rolagem independente dentro de cada aba
        self.scroll_todos = ctk.CTkScrollableFrame(self.aba_todos, fg_color="transparent")
        self.scroll_todos.pack(fill="both", expand=True)

        self.scroll_melhores = ctk.CTkScrollableFrame(self.aba_melhores, fg_color="transparent")
        self.scroll_melhores.pack(fill="both", expand=True)

        self.scroll_aleatorios = ctk.CTkScrollableFrame(self.aba_aleatorios, fg_color="transparent")
        self.scroll_aleatorios.pack(fill="both", expand=True)

        self.scroll_globais = ctk.CTkScrollableFrame(self.aba_globais, fg_color="transparent")
        self.scroll_globais.pack(fill="both", expand=True)

        # ==========================================
        # TELA 3: SORTEIO
        # ==========================================
        self.frame_sorteio = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.label_sorteio = ctk.CTkLabel(self.frame_sorteio, text="🎲 Realizar Sorteio", font=ctk.CTkFont(size=28, weight="bold"))
        self.label_sorteio.pack(pady=(20, 10))

        self.opcao_var = ctk.StringVar(value="1")
        self.radio_1 = ctk.CTkRadioButton(self.frame_sorteio, text="Melhor filme de um país aleatório", variable=self.opcao_var, value="1")
        self.radio_1.pack(pady=5, anchor="w", padx=50)
        self.radio_2 = ctk.CTkRadioButton(self.frame_sorteio, text="Filme aleatório de um país aleatório", variable=self.opcao_var, value="2")
        self.radio_2.pack(pady=5, anchor="w", padx=50)
        self.radio_3 = ctk.CTkRadioButton(self.frame_sorteio, text="Filme totalmente aleatório (Global)", variable=self.opcao_var, value="3")
        self.radio_3.pack(pady=5, anchor="w", padx=50)

        self.btn_executar_sorteio = ctk.CTkButton(self.frame_sorteio, text="SORTEAR!", font=ctk.CTkFont(weight="bold"), command=self.executar_sorteio, width=200, height=40)
        self.btn_executar_sorteio.pack(pady=20)

        self.card_resultado = ctk.CTkFrame(self.frame_sorteio, fg_color=("gray85", "gray15"), corner_radius=10)
        self.card_resultado.pack(pady=10, padx=50, fill="x")
        self.label_resultado = ctk.CTkLabel(self.card_resultado, text="Nenhum filme sorteado ainda.", font=ctk.CTkFont(size=14))
        self.label_resultado.pack(pady=20, padx=20)

        self.mostrar_inicio()

    # ==========================================
    # LÓGICA DE NAVEGAÇÃO E MODO ESCURO
    # ==========================================
    def alternar_modo(self):
        if self.switch_modo.get() == 1:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    def esconder_telas(self):
        self.frame_inicio.grid_forget()
        self.frame_historico.grid_forget()
        self.frame_sorteio.grid_forget()

    def mostrar_inicio(self):
        self.esconder_telas()
        self.frame_inicio.grid(row=0, column=1, sticky="nsew")

    def mostrar_sorteio(self):
        self.esconder_telas()
        self.frame_sorteio.grid(row=0, column=1, sticky="nsew")

    def mostrar_historico(self):
        self.esconder_telas()
        self.frame_historico.grid(row=0, column=1, sticky="nsew")
        self.carregar_arquivos_historico()

    # ==========================================
    # INTEGRAÇÃO: SORTEIO
    # ==========================================
    def executar_sorteio(self):
        opcao = self.opcao_var.get()
        self.label_resultado.configure(text="Sorteando...", text_color="gray")
        self.update()
        
        dados = sorteio.realizar_sorteio(opcao)

        if dados is None:
            self.label_resultado.configure(text="Erro: Base de dados não encontrada.\nRode a atualização primeiro.", text_color="red")
            return

        texto_exibicao = f"🌎 PAÍS: {dados['pais']}  |  🎯 {dados['tipo']}\n\n"
        texto_exibicao += f"🎬 FILME: {dados['titulo']} ({dados['ano']})\n"
        texto_exibicao += f"⭐ Nota IMDb: {dados['nota']}  |  📊 Índice Filmes Global: {dados['indice']:.3f}  |  👥 Votos: {dados['votos']:,}\n"
        texto_exibicao += f"🔎 IMDb ID: {dados['imdb_id']}"

        self.label_resultado.configure(text=texto_exibicao, text_color=("black", "white"), justify="left")

    # ==========================================
    # INTEGRAÇÃO: HISTÓRICO
    # ==========================================
    def desenhar_card(self, container, filme_txt, pais_txt, nota_txt, indice_txt, arquivo_stem):
        """Função auxiliar para desenhar o mesmo card em abas diferentes sem repetir código."""
        card = ctk.CTkFrame(container, fg_color=("gray85", "gray20"))
        card.pack(pady=5, padx=10, fill="x")
        
        if filme_txt and pais_txt:
            texto_principal = f"🎬 {filme_txt} 🌎 ({pais_txt})"
            lbl_titulo = ctk.CTkLabel(card, text=texto_principal, font=ctk.CTkFont(weight="bold", size=14))
            lbl_titulo.pack(anchor="w", padx=15, pady=(10, 0) if nota_txt else 10)
            
            if nota_txt and indice_txt:
                texto_secundario = f"⭐ Nota: {nota_txt}  |  📊 Índice: {indice_txt}"
                lbl_sub = ctk.CTkLabel(card, text=texto_secundario, font=ctk.CTkFont(size=12), text_color="gray")
                lbl_sub.pack(anchor="w", padx=15, pady=(2, 10))
        else:
            pais_antigo = arquivo_stem.replace('_', ' | ')
            texto_card = f"📍 {pais_antigo} (Registro Antigo)"
            lbl_titulo = ctk.CTkLabel(card, text=texto_card, font=ctk.CTkFont(weight="bold", size=14))
            lbl_titulo.pack(anchor="w", padx=15, pady=10)

    def carregar_arquivos_historico(self):
        # Limpa todas as abas antes de carregar
        for scroll in [self.scroll_todos, self.scroll_melhores, self.scroll_aleatorios, self.scroll_globais]:
            for widget in scroll.winfo_children():
                widget.destroy()
        
        pasta_sorteios = Path("sorteios")
        if not pasta_sorteios.exists():
            return

        arquivos = list(pasta_sorteios.glob("*.txt"))
        if not arquivos:
            return
        
        for arquivo in reversed(arquivos):
            pais_txt = filme_txt = nota_txt = indice_txt = modo_txt = ""
            
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    for linha in f:
                        if linha.startswith("PAÍS:"): pais_txt = linha.replace("PAÍS:", "").strip()
                        elif linha.startswith("FILME:"): filme_txt = linha.replace("FILME:", "").strip()
                        elif linha.startswith("NOTA IMDb:"): nota_txt = linha.replace("NOTA IMDb:", "").strip()
                        elif linha.startswith("ÍNDICE:"): indice_txt = linha.replace("ÍNDICE:", "").strip()
                        elif linha.startswith("MODO DO SORTEIO:"): modo_txt = linha.replace("MODO DO SORTEIO:", "").strip().upper()
            except Exception:
                pass
            
            # 1. Desenha o card sempre na aba "Todos"
            self.desenhar_card(self.scroll_todos, filme_txt, pais_txt, nota_txt, indice_txt, arquivo.stem)

            # 2. Verifica a qual outra aba ele pertence e desenha lá também
            if "TOTALMENTE ALEATÓRIO" in modo_txt:
                self.desenhar_card(self.scroll_globais, filme_txt, pais_txt, nota_txt, indice_txt, arquivo.stem)
            
            elif "MELHOR FILME" in modo_txt:
                self.desenhar_card(self.scroll_melhores, filme_txt, pais_txt, nota_txt, indice_txt, arquivo.stem)
            
            elif "ALEATÓRIO" in modo_txt: # Pega o "FILME ALEATÓRIO: PAÍS"
                self.desenhar_card(self.scroll_aleatorios, filme_txt, pais_txt, nota_txt, indice_txt, arquivo.stem)

if __name__ == "__main__":
    app = FilmesGlobalApp()
    app.mainloop()
