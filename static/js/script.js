document.addEventListener('DOMContentLoaded', () => {
    
    // ==========================================
    // NAVEGAÇÃO E TEMA
    // ==========================================
    const navBtns = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.view-section');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            sections.forEach(sec => sec.classList.toggle('active', sec.id === targetId));
            if(targetId === 'tela-historico') carregarHistorico();
            // Evita bug de render do Leaflet quando a aba era display:none
            if(targetId === 'tela-sorteio' && map) setTimeout(() => map.invalidateSize(), 100);
            if(targetId === 'tela-series' && mapSerie) setTimeout(() => mapSerie.invalidateSize(), 100);
            if(targetId === 'tela-livros' && mapLivro) setTimeout(() => mapLivro.invalidateSize(), 100);
            if(targetId === 'tela-musicas' && mapMusica) setTimeout(() => mapMusica.invalidateSize(), 100);
        });
    });

    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIcon = themeToggleBtn.querySelector('i');
    const themeText = themeToggleBtn.querySelector('span');

    if (localStorage.getItem('theme') === 'light') {
        document.body.setAttribute('data-theme', 'light');
        themeIcon.className = 'ph ph-moon';
        themeText.textContent = 'Modo Escuro';
    }

    themeToggleBtn.addEventListener('click', () => {
        if (document.body.getAttribute('data-theme') === 'light') {
            document.body.removeAttribute('data-theme');
            localStorage.setItem('theme', 'dark');
            themeIcon.className = 'ph ph-sun';
            themeText.textContent = 'Modo Claro';
        } else {
            document.body.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
            themeIcon.className = 'ph ph-moon';
            themeText.textContent = 'Modo Escuro';
        }
    });

    // ==========================================
    // MAPA MUNDI (LEAFLET)
    // ==========================================
    let map = null;
    let mapMarker = null;
    let mapSerie = null;
    let mapSerieMarker = null;

    function initMap() {
        if (map) return;
        map = L.map('map-container', {
            zoomControl: false,
            dragging: false,
            scrollWheelZoom: false,
            doubleClickZoom: false
        }).setView([20, 0], 1);

        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);
    }

    function initMapSerie() {
        if (mapSerie) return;
        mapSerie = L.map('map-container-serie', {
            zoomControl: false,
            dragging: false,
            scrollWheelZoom: false,
            doubleClickZoom: false
        }).setView([20, 0], 1);

        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(mapSerie);
    }

    function updateMap(coordenadas) {
        if (!map) initMap();
        if (mapMarker) map.removeLayer(mapMarker);

        if (coordenadas && coordenadas.lat && coordenadas.lon) {
            map.setView([coordenadas.lat, coordenadas.lon], 4, { animate: true, duration: 1.5 });
            
            const customIcon = L.divIcon({
                className: 'custom-pin',
                html: `<div style="background-color: var(--primary-color); width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            mapMarker = L.marker([coordenadas.lat, coordenadas.lon], {icon: customIcon}).addTo(map);
        } else {
            map.setView([20, 0], 1);
        }
    }

    function updateMapSerie(coordenadas) {
        if (!mapSerie) initMapSerie();
        if (mapSerieMarker) mapSerie.removeLayer(mapSerieMarker);

        if (coordenadas && coordenadas.lat && coordenadas.lon) {
            mapSerie.setView([coordenadas.lat, coordenadas.lon], 4, { animate: true, duration: 1.5 });
            
            const customIcon = L.divIcon({
                className: 'custom-pin',
                html: `<div style="background-color: var(--primary-color); width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            mapSerieMarker = L.marker([coordenadas.lat, coordenadas.lon], {icon: customIcon}).addTo(mapSerie);
        } else {
            mapSerie.setView([20, 0], 1);
        }
    }

    let mapLivro = null;
    let mapLivroMarker = null;

    function initMapLivro() {
        if (mapLivro) return;
        mapLivro = L.map('map-container-livro', {
            zoomControl: false,
            dragging: false,
            scrollWheelZoom: false,
            doubleClickZoom: false
        }).setView([20, 0], 1);

        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(mapLivro);
    }

    function updateMapLivro(coordenadas) {
        if (!mapLivro) initMapLivro();
        if (mapLivroMarker) mapLivro.removeLayer(mapLivroMarker);

        if (coordenadas && coordenadas.lat && coordenadas.lon) {
            mapLivro.setView([coordenadas.lat, coordenadas.lon], 4, { animate: true, duration: 1.5 });
            
            const customIcon = L.divIcon({
                className: 'custom-pin',
                html: `<div style="background-color: var(--primary-color); width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            mapLivroMarker = L.marker([coordenadas.lat, coordenadas.lon], {icon: customIcon}).addTo(mapLivro);
        } else {
            mapLivro.setView([20, 0], 1);
        }
    }

    let mapMusica = null;
    let mapMusicaMarker = null;

    function initMapMusica() {
        if (mapMusica) return;
        mapMusica = L.map('map-container-musica', {
            zoomControl: false,
            dragging: false,
            scrollWheelZoom: false,
            doubleClickZoom: false
        }).setView([20, 0], 1);

        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(mapMusica);
    }

    function updateMapMusica(coordenadas) {
        if (!mapMusica) initMapMusica();
        if (mapMusicaMarker) mapMusica.removeLayer(mapMusicaMarker);

        if (coordenadas && coordenadas.lat && coordenadas.lon) {
            mapMusica.setView([coordenadas.lat, coordenadas.lon], 4, { animate: true, duration: 1.5 });
            
            const customIcon = L.divIcon({
                className: 'custom-pin',
                html: `<div style="background-color: #1DB954; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            mapMusicaMarker = L.marker([coordenadas.lat, coordenadas.lon], {icon: customIcon}).addTo(mapMusica);
        } else {
            mapMusica.setView([20, 0], 1);
        }
    }


    // ==========================================
    // LÓGICA DE SORTEIO
    // ==========================================
    const resultadoContainer = document.getElementById('resultado-container');
    const loadingSpinner = document.getElementById('loading-spinner');

    async function realizarSorteioFilme(opcao, usarFiltros = false, buscarDireta = false) {
        let filtros = {};
        if (usarFiltros) {
            filtros = {
                genero: document.getElementById('filtro-genero').value,
                pais: document.getElementById('filtro-pais').value,
                diretor: document.getElementById('filtro-diretor').value,
                ano_min: document.getElementById('filtro-ano-min').value,
                ano_max: document.getElementById('filtro-ano-max').value,
                duracao_min: document.getElementById('filtro-duracao').value,
                nota_min: document.getElementById('filtro-nota').value
            };
        }
        
        if (buscarDireta) {
            filtros.titulo = document.getElementById('filtro-titulo').value;
            filtros.imdb_id = document.getElementById('filtro-imdb-id') ? document.getElementById('filtro-imdb-id').value : '';
        }

        resultadoContainer.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');

        try {
            const res = await fetch('/api/sortear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ opcao: opcao.toString(), filtros: filtros })
            });

            const dados = await res.json();
            if (!res.ok) throw new Error(dados.error || 'Erro ao sortear');

            // Preenche Card
            document.getElementById('res-tipo').textContent = dados.tipo;
            document.getElementById('res-titulo').textContent = dados.titulo;
            document.getElementById('res-ano').textContent = dados.ano;
            document.getElementById('res-duracao').textContent = dados.duracao + " min";
            document.getElementById('res-nota').textContent = dados.nota;
            document.getElementById('res-votos').textContent = parseInt(dados.votos).toLocaleString('pt-BR');
            document.getElementById('res-indice').textContent = (parseFloat(dados.indice) || 0).toFixed(2);
            document.getElementById('res-pais').textContent = dados.pais;
            document.getElementById('res-link').href = `https://www.imdb.com/title/${dados.imdb_id}/`;

            const imgPoster = document.getElementById('res-poster');
            if (dados.poster_url) {
                imgPoster.src = dados.poster_url;
            } else {
                imgPoster.src = "https://via.placeholder.com/240x360/333/999?text=Sem+Capa";
            }

            // Atualiza Mapa
            updateMap(dados.coordenadas);

            // Salvar no histórico
            const histItem = {
                id: Date.now().toString(),
                modo: dados.tipo,
                pais: dados.pais,
                titulo: dados.titulo,
                ano: dados.ano,
                nota: dados.nota,
                indice: dados.indice,
                imdb_id: dados.imdb_id,
                poster_url: dados.poster_url
            };
            salvarNoHistoricoLocal(histItem);

            loadingSpinner.classList.add('hidden');
            resultadoContainer.classList.remove('hidden');

            if(!map) initMap();
            setTimeout(() => map.invalidateSize(), 100);

        } catch (error) {
            alert(error.message);
            loadingSpinner.classList.add('hidden');
        }
    }

    // Ações Rápidas
    const btnQuickMelhor = document.getElementById('btn-quick-melhor');
    const btnQuickAleatorio = document.getElementById('btn-quick-aleatorio');
    const btnQuickGlobal = document.getElementById('btn-quick-global');
    if(btnQuickMelhor) btnQuickMelhor.addEventListener('click', () => realizarSorteioFilme(1, false, false));
    if(btnQuickAleatorio) btnQuickAleatorio.addEventListener('click', () => realizarSorteioFilme(2, false, false));
    if(btnQuickGlobal) btnQuickGlobal.addEventListener('click', () => realizarSorteioFilme(3, false, false));

    // Filtros Personalizados
    const btnSortearFiltros = document.getElementById('btn-sortear-filtros');
    if(btnSortearFiltros) {
        btnSortearFiltros.addEventListener('click', () => {
            const modo = document.querySelector('input[name="modo-filtro"]:checked').value;
            const opcao = modo === 'melhor' ? 1 : 2; // Se não escolheu país, 2 e 1 fazem coisas semelhantes mas o backend lida bem.
            realizarSorteioFilme(opcao, true, false);
        });
    }

    // Busca Direta
    const btnBuscarTitulo = document.getElementById('btn-buscar-titulo');
    if (btnBuscarTitulo) {
        btnBuscarTitulo.addEventListener('click', () => {
            const modo = document.querySelector('input[name="modo-filtro"]:checked').value;
            const opcao = modo === 'melhor' ? 1 : 2;
            realizarSorteioFilme(opcao, true, true);
        });
    }

    // ==========================================
    // LÓGICA DE SORTEIO DE SÉRIES
    // ==========================================
    const resultadoContainerSerie = document.getElementById('resultado-container-serie');
    const loadingSpinnerSerie = document.getElementById('loading-spinner-serie');

    async function realizarSorteioSerie(opcao, usarFiltros = false, buscarDireta = false) {
        let filtros = {};
        if (usarFiltros) {
            filtros = {
                genero: document.getElementById('filtro-serie-genero').value,
                pais: document.getElementById('filtro-serie-pais').value,
                diretor: document.getElementById('filtro-serie-diretor').value,
                ano_min: document.getElementById('filtro-serie-ano-min').value,
                ano_max: document.getElementById('filtro-serie-ano-max').value,
                nota_min: document.getElementById('filtro-serie-nota').value
            };
        }
        
        if (buscarDireta) {
            filtros.titulo = document.getElementById('filtro-serie-titulo').value;
            filtros.imdb_id = document.getElementById('filtro-serie-imdb-id') ? document.getElementById('filtro-serie-imdb-id').value : '';
        }

        resultadoContainerSerie.classList.add('hidden');
        loadingSpinnerSerie.classList.remove('hidden');

        try {
            const res = await fetch('/api/sortear_serie', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ opcao: opcao.toString(), filtros: filtros })
            });

            const dados = await res.json();
            if (!res.ok) throw new Error(dados.error || 'Erro ao sortear série');

            document.getElementById('res-serie-tipo').textContent = dados.tipo;
            document.getElementById('res-serie-titulo').textContent = dados.titulo;
            document.getElementById('res-serie-ano').textContent = dados.ano;
            document.getElementById('res-serie-duracao').textContent = dados.duracao;
            document.getElementById('res-serie-nota').textContent = dados.nota;
            document.getElementById('res-serie-votos').textContent = parseInt(dados.votos).toLocaleString('pt-BR');
            document.getElementById('res-serie-indice').textContent = (parseFloat(dados.indice) || 0).toFixed(2);
            document.getElementById('res-serie-pais').textContent = dados.pais;
            
            const linkSerie = document.getElementById('res-serie-link');
            if (dados.tmdb_id) {
                linkSerie.href = `https://www.themoviedb.org/tv/${dados.tmdb_id}`;
            } else if (dados.imdb_id) {
                linkSerie.href = `https://www.imdb.com/title/${dados.imdb_id}/`;
            }

            const imgPosterSerie = document.getElementById('res-serie-poster');
            if (dados.poster_url) {
                imgPosterSerie.src = dados.poster_url;
            } else {
                imgPosterSerie.src = "https://via.placeholder.com/240x360/333/999?text=Sem+Capa";
            }

            updateMapSerie(dados.coordenadas);

            // Salvar no histórico local
            const histItem = {
                id: Date.now().toString(),
                modo: dados.tipo,
                pais: dados.pais,
                titulo: dados.titulo,
                ano: dados.ano,
                nota: dados.nota,
                indice: dados.indice,
                imdb_id: dados.imdb_id || dados.tmdb_id,
                poster_url: dados.poster_url
            };
            salvarNoHistoricoLocal(histItem);

            loadingSpinnerSerie.classList.add('hidden');
            resultadoContainerSerie.classList.remove('hidden');

            if(!mapSerie) initMapSerie();
            setTimeout(() => mapSerie.invalidateSize(), 100);

        } catch (error) {
            alert(error.message);
            loadingSpinnerSerie.classList.add('hidden');
        }
    }

    // Ações Rápidas Séries
    const btnQuickSerieMelhor = document.getElementById('btn-quick-serie-melhor');
    const btnQuickSerieAleatorio = document.getElementById('btn-quick-serie-aleatorio');
    const btnQuickSerieGlobal = document.getElementById('btn-quick-serie-global');
    if(btnQuickSerieMelhor) btnQuickSerieMelhor.addEventListener('click', () => realizarSorteioSerie(1, false, false));
    if(btnQuickSerieAleatorio) btnQuickSerieAleatorio.addEventListener('click', () => realizarSorteioSerie(2, false, false));
    if(btnQuickSerieGlobal) btnQuickSerieGlobal.addEventListener('click', () => realizarSorteioSerie(3, false, false));

    // Filtros Personalizados Séries
    const btnSortearSerie = document.getElementById('btn-sortear-serie');
    if(btnSortearSerie) {
        btnSortearSerie.addEventListener('click', () => {
            const modo = document.querySelector('input[name="modo-filtro-serie"]:checked').value;
            const opcao = modo === 'melhor' ? 1 : 2;
            realizarSorteioSerie(opcao, true, false);
        });
    }

    // Busca Direta Séries
    const btnBuscarSerieTitulo = document.getElementById('btn-buscar-serie-titulo');
    if (btnBuscarSerieTitulo) {
        btnBuscarSerieTitulo.addEventListener('click', () => {
            const modo = document.querySelector('input[name="modo-filtro-serie"]:checked').value;
            const opcao = modo === 'melhor' ? 1 : 2;
            realizarSorteioSerie(opcao, true, true);
        });
    }

    // ==========================================
    // LÓGICA DE SORTEIO DE LIVROS
    // ==========================================
    const resultadoContainerLivro = document.getElementById('resultado-container-livro');
    const loadingSpinnerLivro = document.getElementById('loading-spinner-livro');

    async function realizarSorteioLivro(opcao, usarFiltros = false, buscarDireta = false) {
        let filtros = {};
        if (usarFiltros) {
            filtros = {
                assunto: document.getElementById('filtro-livro-assunto').value,
                autor: document.getElementById('filtro-livro-autor').value,
                pais: document.getElementById('filtro-livro-pais').value
            };
        }
        
        if (buscarDireta) {
            filtros.titulo = document.getElementById('filtro-livro-titulo').value;
            filtros.id = document.getElementById('filtro-livro-id') ? document.getElementById('filtro-livro-id').value : '';
        }

        resultadoContainerLivro.classList.add('hidden');
        loadingSpinnerLivro.classList.remove('hidden');

        try {
            const res = await fetch('/api/sortear_livro', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ opcao: opcao.toString(), filtros: filtros })
            });

            const dados = await res.json();
            if (!res.ok) throw new Error(dados.error || 'Erro ao sortear livro');

            document.getElementById('res-livro-tipo').textContent = dados.tipo || 'LIVRO';
            document.getElementById('res-livro-titulo').textContent = dados.titulo;
            document.getElementById('res-livro-autor').textContent = dados.autor;
            document.getElementById('res-livro-ano').textContent = dados.ano;
            document.getElementById('res-livro-paginas').textContent = dados.paginas;
            document.getElementById('res-livro-nota').textContent = dados.nota;
            document.getElementById('res-livro-pais').textContent = dados.pais || 'Desconhecido';
            document.getElementById('res-livro-sinopse').textContent = dados.sinopse;
            
            const link = document.getElementById('res-livro-link');
            if (dados.link) {
                link.href = dados.link;
                link.style.display = 'inline-block';
            } else {
                link.style.display = 'none';
            }

            const imgCapa = document.getElementById('res-livro-capa');
            if (dados.capa_url) {
                imgCapa.src = dados.capa_url;
            } else {
                imgCapa.src = "https://via.placeholder.com/240x360/333/999?text=Sem+Capa";
            }

            updateMapLivro(dados.coordenadas);

            // Salvar no histórico local
            const histItem = {
                id: Date.now().toString(),
                modo: dados.tipo,
                pais: dados.pais,
                titulo: dados.titulo,
                ano: dados.ano,
                nota: dados.nota,
                indice: 0,
                link: dados.link,
                poster_url: dados.capa_url,
                is_book: true
            };
            salvarNoHistoricoLocal(histItem);

            loadingSpinnerLivro.classList.add('hidden');
            resultadoContainerLivro.classList.remove('hidden');

            if(!mapLivro) initMapLivro();
            setTimeout(() => mapLivro.invalidateSize(), 100);

        } catch (error) {
            alert(error.message);
            loadingSpinnerLivro.classList.add('hidden');
        }
    }

    // Ações Rápidas Livros
    const btnQuickLivroAleatorio = document.getElementById('btn-quick-livro-aleatorio');
    const btnQuickLivroGlobal = document.getElementById('btn-quick-livro-global');
    if(btnQuickLivroAleatorio) btnQuickLivroAleatorio.addEventListener('click', () => realizarSorteioLivro(2, false, false));
    if(btnQuickLivroGlobal) btnQuickLivroGlobal.addEventListener('click', () => realizarSorteioLivro(3, false, false));

    // Filtros Personalizados Livros
    const btnSortearLivro = document.getElementById('btn-sortear-livro');
    if(btnSortearLivro) {
        btnSortearLivro.addEventListener('click', () => {
            const opcao = 2; // Default to Aleatório
            realizarSorteioLivro(opcao, true, false);
        });
    }

    // Busca Direta Livros
    const btnBuscarLivroTitulo = document.getElementById('btn-buscar-livro-titulo');
    if (btnBuscarLivroTitulo) {
        btnBuscarLivroTitulo.addEventListener('click', () => {
            const opcao = 2; // Default to Aleatório
            realizarSorteioLivro(opcao, true, true);
        });
    }

    // ==========================================
    // LÓGICA DE SORTEIO DE MÚSICAS
    // ==========================================
    // ==========================================
    // LÓGICA DE SORTEIO DE MÚSICAS
    // ==========================================
    const resultadoContainerMusica = document.getElementById('resultado-container-musica');
    const loadingSpinnerMusica = document.getElementById('loading-spinner-musica');

    async function realizarSorteioMusica(opcao, usarFiltros = false, buscarDireta = false) {
        let filtros = {};
        if (usarFiltros) {
            filtros = {
                energia: document.getElementById('filtro-musica-energia') ? document.getElementById('filtro-musica-energia').value : '',
                dancabilidade: document.getElementById('filtro-musica-dancabilidade') ? document.getElementById('filtro-musica-dancabilidade').value : '',
                artista: document.getElementById('filtro-musica-artista').value,
                epoca_min: document.getElementById('filtro-musica-ano-min').value,
                epoca_max: document.getElementById('filtro-musica-ano-max').value
            };
        }
        
        if (buscarDireta) {
            filtros.titulo = document.getElementById('filtro-musica-titulo') ? document.getElementById('filtro-musica-titulo').value : '';
            filtros.id = document.getElementById('filtro-musica-id') ? document.getElementById('filtro-musica-id').value : '';
        }

        resultadoContainerMusica.classList.add('hidden');
        loadingSpinnerMusica.classList.remove('hidden');

        try {
            const res = await fetch('/api/sortear_musica', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ opcao: opcao.toString(), filtros: filtros })
            });

            const dados = await res.json();
            if (!res.ok) throw new Error(dados.error || 'Erro ao sortear música');

            document.getElementById('res-musica-tipo').textContent = dados.tipo || 'MÚSICA';
            document.getElementById('res-musica-titulo').textContent = dados.titulo;
            document.getElementById('res-musica-artista').textContent = dados.artista;
            document.getElementById('res-musica-album').textContent = dados.album;
            document.getElementById('res-musica-ano').textContent = dados.ano;
            document.getElementById('res-musica-pais').textContent = dados.pais || 'Desconhecido';
            
            const link = document.getElementById('res-musica-link');
            if (dados.link) {
                link.href = dados.link;
                link.style.display = 'inline-block';
            } else {
                link.style.display = 'none';
            }

            const imgCapa = document.getElementById('res-musica-capa');
            if (dados.capa_url) {
                imgCapa.src = dados.capa_url;
            } else {
                imgCapa.src = "https://via.placeholder.com/240x360/333/999?text=Sem+Capa";
            }

            updateMapMusica(dados.coordenadas);

            // Salvar no histórico local
            const histItem = {
                id: Date.now().toString(),
                modo: dados.tipo,
                pais: dados.pais,
                titulo: dados.titulo,
                ano: dados.ano,
                nota: '-', // musica não tem nota
                indice: 0,
                link: dados.link,
                poster_url: dados.capa_url,
                is_music: true
            };
            salvarNoHistoricoLocal(histItem);

            loadingSpinnerMusica.classList.add('hidden');
            resultadoContainerMusica.classList.remove('hidden');

            if(!mapMusica) initMapMusica();
            setTimeout(() => mapMusica.invalidateSize(), 100);

        } catch (error) {
            alert(error.message);
            loadingSpinnerMusica.classList.add('hidden');
        }
    }

    // Ações Rápidas Músicas
    const btnQuickMusicaAleatorio = document.getElementById('btn-quick-musica-aleatorio');
    const btnQuickMusicaGlobal = document.getElementById('btn-quick-musica-global');
    if(btnQuickMusicaAleatorio) btnQuickMusicaAleatorio.addEventListener('click', () => realizarSorteioMusica(2, false, false));
    if(btnQuickMusicaGlobal) btnQuickMusicaGlobal.addEventListener('click', () => realizarSorteioMusica(3, false, false));

    // Filtros Personalizados Músicas
    const btnSortearMusica = document.getElementById('btn-sortear-musica');
    if(btnSortearMusica) {
        btnSortearMusica.addEventListener('click', () => {
            const opcao = 2; // Default to Aleatório
            realizarSorteioMusica(opcao, true, false);
        });
    }

    // Busca Direta Músicas
    const btnBuscarMusicaTitulo = document.getElementById('btn-buscar-musica-titulo');
    if (btnBuscarMusicaTitulo) {
        btnBuscarMusicaTitulo.addEventListener('click', () => {
            const opcao = 2; // Default to Aleatório
            realizarSorteioMusica(opcao, true, true);
        });
    }

    // ==========================================
    // HISTÓRICO
    // ==========================================
    const tabBtns = document.querySelectorAll('.tab-btn');
    const historicoList = document.getElementById('historico-list');
    const historicoEmpty = document.getElementById('historico-empty');
    let todosSorteios = [];

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderizarHistorico(btn.getAttribute('data-tab'));
        });
    });

    function salvarNoHistoricoLocal(item) {
        let hist = JSON.parse(localStorage.getItem('kinomap_historico') || '[]');
        // Limita o histórico aos últimos 100 sorteios para não encher o localStorage
        if (hist.length >= 100) {
            hist.pop();
        }
        hist.unshift(item);
        localStorage.setItem('kinomap_historico', JSON.stringify(hist));
    }

    function carregarHistorico() {
        try {
            todosSorteios = JSON.parse(localStorage.getItem('kinomap_historico') || '[]');
            const btnAtivo = document.querySelector('.tab-btn.active');
            const abaAtiva = btnAtivo ? btnAtivo.getAttribute('data-tab') : 'todos';
            renderizarHistorico(abaAtiva);
        } catch (error) {
            console.error('Erro ao carregar histórico:', error);
            todosSorteios = [];
            renderizarHistorico('todos');
        }
    }

    function renderizarHistorico(filtro) {
        historicoList.innerHTML = '';
        let filtrados = todosSorteios;

        if (filtro === 'melhores') filtrados = todosSorteios.filter(s => s.modo && s.modo.includes('MELHOR'));
        else if (filtro === 'aleatorios') filtrados = todosSorteios.filter(s => s.modo && s.modo.includes('ALEATÓRI'));
        else if (filtro === 'globais') filtrados = todosSorteios.filter(s => s.modo && (s.modo.includes('TOTALMENTE') || s.modo.includes('GLOBAL')));

        if (filtrados.length === 0) {
            historicoEmpty.classList.remove('hidden');
            return;
        }

        historicoEmpty.classList.add('hidden');

        filtrados.forEach(item => {
            if (item.titulo !== 'Registro Antigo') {
                const imgUrl = item.poster_url || "https://via.placeholder.com/240x360/333/999?text=Sem+Capa";
                const isImdb = item.imdb_id && String(item.imdb_id).startsWith('tt');
                
                let linkUrl = '#';
                let linkText = 'Abrir';

                if (item.is_music) {
                    linkUrl = item.link || '#';
                    linkText = 'Ouvir no Spotify';
                } else if (item.is_book) {
                    linkUrl = item.link || '#';
                    linkText = 'Abrir no OpenLibrary';
                } else if (isImdb) {
                    linkUrl = `https://www.imdb.com/title/${item.imdb_id}/`;
                    linkText = 'Abrir no IMDb';
                } else if (item.imdb_id) {
                    linkUrl = `https://www.themoviedb.org/tv/${item.imdb_id}`;
                    linkText = 'Abrir no TMDb';
                }

                const card = document.createElement('div');
                card.className = 'movie-card';
                card.innerHTML = `
                    <img src="${imgUrl}" alt="Capa">
                    <div class="movie-info">
                        <span class="badge" style="align-self: flex-start; margin-bottom: 0.5rem; font-size: 0.6rem;">${item.modo || 'Sorteio'}</span>
                        <h3>${item.titulo}</h3>
                        <div class="details">${item.ano || ''}</div>
                        <div class="stats">
                            <span title="Nota"><i class="ph ph-star-fill" style="color:#f1c40f;"></i> ${item.nota || '?'}</span>
                            ${(item.is_book || item.is_music) ? '' : `<span title="Nota KM" style="color: var(--primary-color); font-weight: bold; margin-left: auto;">KM: ${(parseFloat(item.indice) || 0).toFixed(2)}</span>`}
                        </div>
                        <div style="font-size: 0.75rem; margin-top: 0.2rem; color: #eee;">
                            <i class="ph ph-map-pin"></i> ${item.pais || 'Desconhecido'}
                        </div>
                        <a href="${linkUrl}" target="_blank" class="btn-imdb">${linkText}</a>
                    </div>
                `;
                historicoList.appendChild(card);
            }
        });
    }

});

// Autocomplete customizado para filmes
function setupCustomAutocomplete(inputId, dropdownId, hiddenId, tipo) {
    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(dropdownId);
    const hidden = document.getElementById(hiddenId);
    if(!input || !dropdown) return;

    let debounceTimer;
    
    input.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const query = e.target.value.trim();
        if(hidden) hidden.value = ""; // Limpa o ID se o usuário digitar algo novo
        
        if(query.length < 1) {
            dropdown.classList.add('hidden');
            return;
        }
        
        // Atraso removido
        debounceTimer = setTimeout(async () => {
            try {
                const res = await fetch('/api/autocomplete?q=' + encodeURIComponent(query) + '&tipo=' + tipo);
                const data = await res.json();
                
                dropdown.innerHTML = '';
                if(data.length === 0) {
                    dropdown.classList.add('hidden');
                    return;
                }

                data.forEach(item => {
                    const li = document.createElement('li');
                    li.innerHTML = `<span class="dropdown-title">${item.title}</span> <span class="dropdown-year">(${item.year || 'N/A'})</span>`;
                    li.addEventListener('click', () => {
                        input.value = item.title;
                        if(hidden) hidden.value = item.id;
                        dropdown.classList.add('hidden');
                    });
                    dropdown.appendChild(li);
                });
                dropdown.classList.remove('hidden');
            } catch(e) { console.error(e); }
        }, 0); 
    });

    // Esconde o dropdown ao clicar fora
    document.addEventListener('click', (e) => {
        if(!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });
}

// Mantendo o setup antigo de datalist para series/outros (ainda n atualizado)
function setupAutocomplete(inputId, datalistId, tipo) {
    const input = document.getElementById(inputId);
    const datalist = document.getElementById(datalistId);
    if(!input || !datalist) return;
    let debounceTimer;
    input.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const query = e.target.value.trim();
        if(query.length < 1) return;
        debounceTimer = setTimeout(async () => {
            try {
                const res = await fetch('/api/autocomplete?q=' + encodeURIComponent(query) + '&tipo=' + tipo);
                const data = await res.json();
                datalist.innerHTML = '';
                data.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.title;
                    option.textContent = item.title + ' (' + (item.year || 'N/A') + ')';
                    datalist.appendChild(option);
                });
            } catch(e) { console.error(e); }
        }, 300);
    });
}

setupCustomAutocomplete('filtro-titulo', 'custom-autocomplete-filmes', 'filtro-imdb-id', 'movie');
setupCustomAutocomplete('filtro-serie-titulo', 'custom-autocomplete-series', 'filtro-serie-imdb-id', 'serie');
setupCustomAutocomplete('filtro-livro-titulo', 'custom-autocomplete-livros', 'filtro-livro-id', 'livro');
setupCustomAutocomplete('filtro-musica-titulo', 'custom-autocomplete-musicas', 'filtro-musica-id', 'musica');
