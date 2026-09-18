# 🎵 BOT-Discord - Music, Entertainment & Deals Bot

Um bot Discord completo desenvolvido em Python com suporte para reprodução de música, boas-vindas automáticas, alertas de feriados e busca de promoções de games!

## ✨ Funcionalidades

### 🎵 Reprodução de Música
- `/play <consulta>` - Toca ou adiciona música à fila
- `/skip` - Pula para próxima música
- `/pause` - Pausa reprodução
- `/resume` - Retoma reprodução
- `/stop` - Para e limpa fila
- `/leave` - Desconecta do canal de voz
- `/queue` - Mostra fila de música (com paginação)
- `/loop <off|track|queue>` - Define modo de repetição

### 👋 Boas-vindas Automáticas
- `/welcome set-message <mensagem>` - Define mensagem de boas-vindas personalizada
- `/welcome set-channel <canal>` - Define canal para boas-vindas
- `/welcome enable` - Ativa boas-vindas
- `/welcome list` - Lista histórico de boas-vindas

**Variáveis disponíveis na mensagem:**
- `{mention}` - Menção do usuário
- `{username}` - Nome do usuário
- `{server}` - Nome do servidor
- `{total_members}` - Quantidade total de membros

### 🎉 Alertas de Feriados
- `/holidays next [limit]` - Mostra próximos feriados (até 10)
- `/holidays today` - Verifica se hoje é feriado
- `/holidays reminder <dias>` - Define alertas com antecedência
- `/holidays notify` - Envia notificação de feriados próximos

**Feriados suportados:**
- Todos os feriados brasileiros fixos (Ano Novo, Tiradentes, etc)
- Feriados móveis calculados dinamicamente (Páscoa, Corpus Christi, etc)

### 🎮 Busca de Promoções de Games
- `/games search <título>` - Busca um game com descontos
- `/games deals <desconto>` - Mostra games com desconto mínimo
- `/games follow <jogo>` - Recebe notificações de promoções
- `/games trending` - Mostra games em alta com desconto

**Exemplo:**
```
/games deals 70  # Mostra games com 70%+ de desconto
/games search "Elden Ring"  # Busca promoções do jogo
```

## 🚀 Instalação

### Pré-requisitos
- Python 3.11+
- Java (para Lavalink)
- Discord Bot Token
- Docker (opcional, para facilitar)

### Setup Local

1. **Clone o repositório:**
```bash
git clone <seu-repositorio>
cd BOT-Discord
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Edite .env e adicione seu DISCORD_TOKEN
```

4. **Inicie o Lavalink** (em outro terminal):
```bash
# Use Docker ou execute o Lavalink diretamente
docker run -d -p 2333:2333 --name lavalink fredboat/lavalink
```

5. **Inicie o bot:**
```bash
python -m bot.src.bot
```

### Setup com Docker

```bash
docker-compose up -d
```

Isso iniciará tanto o Lavalink quanto o Bot automaticamente.

## 📁 Estrutura do Projeto

```
BOT-Discord/
├── bot/
│   ├── src/
│   │   ├── bot.py              # Ponto de entrada
│   │   ├── settings.py         # Configurações
│   │   ├── commands/           # Comandos do bot
│   │   │   ├── music.py        # Reprodução de música
│   │   │   ├── playlist.py     # Gerenciamento de playlists
│   │   │   ├── utility.py      # Comandos utilitários
│   │   │   ├── welcome.py      # Boas-vindas
│   │   │   ├── holidays.py     # Feriados
│   │   │   └── games.py        # Promoções de games
│   │   ├── core/               # Lógica central
│   │   │   ├── client.py       # Cliente Discord
│   │   │   ├── manager.py      # Gerenciador de música
│   │   │   ├── scheduler.py    # Agendador de tarefas
│   │   │   └── lavalink.py     # Integração Lavalink
│   │   ├── events/             # Listeners de eventos
│   │   │   └── server_events.py # Eventos do servidor
│   │   ├── services/           # Integrações externas
│   │   │   └── game_promotions.py # API de promoções
│   │   ├── storage/            # Banco de dados
│   │   │   └── database.py     # SQLite
│   │   ├── data/               # Dados estáticos
│   │   │   └── holidays.py     # Feriados
│   │   └── views/              # Componentes UI
│   └── tests/                  # Testes automatizados
├── requirements.txt            # Dependências Python
├── pyproject.toml              # Configuração do projeto
├── docker-compose.yml          # Orquestração Docker
├── application.yml             # Config Lavalink
└── README.md                   # Esta documentação
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```bash
# Obrigatório
DISCORD_TOKEN=seu_token_aqui

# Lavalink
LAVALINK_HOST=lavalink          # ou localhost para desenvolvimento
LAVALINK_PORT=2333
LAVALINK_PASSWORD=youshallnotpass

# Opcional
GUILD_IDS=123456789,987654321   # Sincroniza comandos mais rápido
```

### Configurações de Lavalink (application.yml)

- Porta: 2333
- Fontes de música habilitadas: SoundCloud, YouTube (via plugin)
- Filtros: todos habilitados (volume, equalizer, karaoke, etc)

## 📊 Banco de Dados

O bot utiliza SQLite para armazenar:
- Mensagens de boas-vindas personalizadas
- Histórico de boas-vindas
- Alertas de feriados
- Seguidores de promoções
- Histórico de promoções

Database: `data/bot.db` (criado automaticamente)

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=bot tests/

# Executar teste específico
pytest bot/tests/test_manager.py
```

## 🛠️ Desenvolvimento

### Adicionando um novo comando

1. Crie um arquivo em `bot/src/commands/seu_comando.py`
2. Defina a classe `SeuCog(commands.Cog)`
3. Adicione `sua_comando` na lista `cogs_to_load` em `client.py`

### Adicionando uma tarefa agendada

```python
async def minha_tarefa():
    logger.info("Executando minha tarefa!")

# Executar diariamente às 10:00
self.scheduler.schedule_daily_task(minha_tarefa, hour=10, minute=0)

# Executar a cada 6 horas
self.scheduler.schedule_interval_task(minha_tarefa, hours=6)
```

### Usando o banco de dados

```python
from bot.src.storage.database import Database

db = Database()
db.connect()

# Salvar dados
db.save_welcome_message(guild_id, channel_id, "Bem-vindo!")

# Recuperar dados
welcome = db.get_welcome_message(guild_id)
```

## 🐛 Troubleshooting

### Bot não conecta ao Lavalink
- Verifique se Lavalink está rodando: `docker ps`
- Verifique credenciais em `.env`
- Verifique se porta 2333 está aberta

### Comandos não aparecem no Discord
- Aguarde sincronização (até 1 hora) ou especifique `GUILD_IDS`
- Tente sair e entrar novamente no servidor
- Verifique permissões do bot no servidor

### Bot não tem permissão para enviar mensagens
- Confira permissões do canal (@BotName)
- Verifique role do bot está acima dos usuários normais

## 📝 Logs

Logs são salvos em `logs/bot.log` com rotação automática.

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:
1. Faça fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a MIT License.

## 👨‍💻 Autor

Desenvolvido com ❤️ por [seu-nome]

## 🔗 Links Úteis

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Wavelink Documentation](https://wavelink.readthedocs.io/)
- [Lavalink Server](https://github.com/lavalink-devs/Lavalink)
- [CheapShark API](https://apidocs.cheapshark.com/)

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique o arquivo de logs: `logs/bot.log`
2. Abra uma issue no GitHub
3. Entre em contato no Discord

---

**Bom uso! 🎉**
