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

    function initMap() {
        if (map) return;
        map = L.map('map-container', {
            zoomControl: false,
            dragging: false,
            scrollWheelZoom: false,
            doubleClickZoom: false
        }).setView([20, 0], 1); // Visão global

        // Usando OpenStreetMap (totalmente gratuito e sem chave de API)
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
    }

    function updateMap(coordenadas) {
        if (!map) initMap();
        if (mapMarker) map.removeLayer(mapMarker);

        if (coordenadas && coordenadas.lat && coordenadas.lon) {
            map.setView([coordenadas.lat, coordenadas.lon], 4, { animate: true, duration: 1.5 });
            
            // Cria um pin bonito e customizado
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


    // ==========================================
    // LÓGICA DE SORTEIO
    // ==========================================
    const btnSortear = document.getElementById('btn-sortear');
    const resultadoContainer = document.getElementById('resultado-container');
    const loadingSpinner = document.getElementById('loading-spinner');

    btnSortear.addEventListener('click', async () => {
        const opcao = document.querySelector('input[name="opcao-sorteio"]:checked').value;
        const filtros = {
            genero: document.getElementById('filtro-genero').value,
            ano_min: document.getElementById('filtro-ano-min').value,
            ano_max: document.getElementById('filtro-ano-max').value,
            duracao_min: document.getElementById('filtro-duracao').value,
            nota_min: document.getElementById('filtro-nota').value
        };
        
        resultadoContainer.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');
        btnSortear.disabled = true;

        try {
            const res = await fetch('/api/sortear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ opcao: opcao, filtros: filtros })
            });

            const dados = await res.json();
            if (!res.ok) throw new Error(dados.error || 'Erro ao sortear');

            // Preenche Card Netflix
            document.getElementById('res-tipo').textContent = dados.tipo;
            document.getElementById('res-titulo').textContent = dados.titulo;
            document.getElementById('res-ano').textContent = dados.ano;
            document.getElementById('res-duracao').textContent = dados.duracao + " min";
            document.getElementById('res-nota').textContent = dados.nota;
            document.getElementById('res-votos').textContent = parseInt(dados.votos).toLocaleString('pt-BR');
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

            loadingSpinner.classList.add('hidden');
            resultadoContainer.classList.remove('hidden');

            // Inicializa mapa se não estava
            if(!map) initMap();
            setTimeout(() => map.invalidateSize(), 100);

        } catch (error) {
            alert(error.message);
            loadingSpinner.classList.add('hidden');
        } finally {
            btnSortear.disabled = false;
        }
    });

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

    async function carregarHistorico() {
        try {
            const res = await fetch('/api/historico');
            todosSorteios = await res.json();
            const abaAtiva = document.querySelector('.tab-btn.active').getAttribute('data-tab');
            renderizarHistorico(abaAtiva);
        } catch (error) {
            console.error('Erro:', error);
        }
    }

    function renderizarHistorico(filtro) {
        historicoList.innerHTML = '';
        let filtrados = todosSorteios;

        if (filtro === 'melhores') filtrados = todosSorteios.filter(s => s.modo && s.modo.includes('MELHOR FILME'));
        else if (filtro === 'aleatorios') filtrados = todosSorteios.filter(s => s.modo && s.modo.includes('FILME ALEATÓRIO:'));
        else if (filtro === 'globais') filtrados = todosSorteios.filter(s => s.modo && s.modo.includes('TOTALMENTE ALEATÓRIO'));

        if (filtrados.length === 0) {
            historicoEmpty.classList.remove('hidden');
            return;
        }

        historicoEmpty.classList.add('hidden');

        filtrados.forEach(item => {
            if (item.titulo !== 'Registro Antigo') {
                const imgUrl = item.poster_url || "https://via.placeholder.com/240x360/333/999?text=Sem+Capa";
                
                const card = document.createElement('div');
                card.className = 'movie-card';
                card.innerHTML = `
                    <img src="${imgUrl}" alt="Capa">
                    <div class="movie-info">
                        <span class="badge" style="align-self: flex-start; margin-bottom: 0.5rem; font-size: 0.6rem;">${item.modo}</span>
                        <h3>${item.titulo}</h3>
                        <div class="details">${item.ano}</div>
                        <div class="stats">
                            <span><i class="ph ph-star-fill" style="color:#f1c40f;"></i> ${item.nota}</span>
                        </div>
                        <div style="font-size: 0.75rem; margin-top: 0.2rem; color: #eee;">
                            <i class="ph ph-map-pin"></i> ${item.pais}
                        </div>
                        <a href="https://www.imdb.com/title/${item.imdb_id}/" target="_blank" class="btn-imdb">Abrir no IMDb</a>
                    </div>
                `;
                historicoList.appendChild(card);
            }
        });
    }

});
