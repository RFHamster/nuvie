# Nuvie Tech Challenge

## 1. Visão Geral do Projeto

HealthSync é um sistema de backend robusto e escalável para o gerenciamento de dados de pacientes, desenvolvido como parte de um desafio técnico para a posição de Engenheiro de Software com foco em Backend.

O principal objetivo foi projetar e implementar uma solução que não apenas cumprisse os requisitos essenciais, como a manipulação de dados e autenticação, mas que também demonstrasse excelência em práticas de engenharia de software, utilizando uma arquitetura de microsserviços containerizada.

## 2. Funcionalidades Implementadas

| Requisito | Status | Detalhes |
| :--- | :---: | :--- |
| **Arquitetura de Microsserviços** | ✅ | O sistema é dividido em dois serviços independentes: **Users** e **Patients**. |
| **Framework FastAPI** | ✅ | Todas as APIs foram construídas utilizando FastAPI, aproveitando sua alta performance e recursos modernos. |
| **Manipulação de Dados** | ✅ | Endpoints para criação e consulta de pacientes com validação de dados via Pydantic. |
| **Autenticação e Autorização** | ✅ | Sistema de autenticação baseado em JWT, gerenciado pelo microsserviço de **Users**. |
| **Documentação da API (Swagger)** | ✅ | Cada microsserviço expõe sua própria documentação interativa e completa. |
| **Containerização (Docker)** | ✅ | Todo o ambiente (serviços, banco de dados, proxy) é gerenciado pelo Docker e Docker Compose. |
| **Gateway de API e Load Balancer** | ✅ | Um NGINX atua como Reverse Proxy, unificando o acesso aos microsserviços e atuando como ponto de entrada único. |

## 3. Arquitetura do Sistema

A solução foi projetada seguindo os princípios da arquitetura de microsserviços para garantir escalabilidade, resiliência e manutenibilidade.
Snippet de código

Componentes:

- **NGINX (Reverse Proxy)**: Atua como o ponto de entrada único (gateway) para todas as requisições externas. Ele roteia o tráfego para o microsserviço apropriado (/users/* ou /patients/*) e pode atuar como um load balancer caso existam múltiplas instâncias de um mesmo serviço.

- **Microsserviço de Usuários (users-service)**: Responsável por gerenciar o cadastro, login e a geração de tokens de autenticação (JWT).

- **Microsserviço de Pacientes** (patients-service): Gerencia todas as operações CRUD relacionadas aos dados dos pacientes. O acesso aos seus endpoints é protegido e requer um token JWT válido.

- **PostgreSQL (Banco de Dados)**: Banco de dados relacional centralizado, utilizando schemas (users, patients) para garantir o isolamento lógico dos dados de cada microsserviço.

- **Repositório nuvie-db**: Um repositório Git desacoplado que contém todos os modelos de dados (SQLAlchemy) e as migrações (Alembic) do banco de dados. Essa abordagem centraliza a gestão do schema do DB, facilitando a consistência e a automação das migrações.


## 4. Stack de Tecnologias

- Backend: Python 3.11+, FastAPI
- Validação de Dados: Pydantic
- Banco de Dados: PostgreSQL
- ORM & Migrations: SQLAlchemy, Alembic
- Containerização: Docker, Docker Compose
- Gateway/Proxy: NGINX
- Autenticação: JWT (JSON Web Tokens)

## 5. Como Executar o Projeto

O ambiente é 100% containerizado, simplificando drasticamente o processo de setup.

### Passo a Passo

1. **Configure as Variáveis de Ambiente:**

Crie um arquivo `.env` na raiz do projeto, a partir do exemplo fornecido no email.

2. **Inicie os Contêineres:**

Suba toda a stack (serviços, banco de dados e NGINX) com um único comando.
```bash
docker-compose up -d --build
```

3. **Aplique as Migrações do Banco de Dados:**

Com os contêineres em execução, execute o script para criar as tabelas e schemas no banco de dados (necessário estar no [nuvie-db](https://github.com/RFHamster/nuvie-db)).

```bash
bash ./scripts/apply-migrations.sh
```

Este script irá executar os comandos do Alembic contidos no repositório `nuvie-db`.

4. **Rode o script de inserção de Pacientes (opcional):**

Se quiser alguns pacientes já mockados e tiver o uv conifigurado rode:

```bash
uv run scripts/client/patient_insertion.py
```

Para instalar UV segue o [link](https://docs.astral.sh/uv/getting-started/installation/), com o uv pode-se rodar uv sync para baixar os pacotes e depois rodar o script.

5. Crie seu usuário:

Utilize da rota de criação de usuários para conseguir acessar a aplicação

A aplicação agora está totalmente funcional e acessível!

## 6. Utilização e Endpoints da API

O ponto de entrada para todas as chamadas da API é o NGINX, na porta 8000.

    URL Base: http://localhost:8000

Mas para acessar as documentações pode-se entrar em qualquer um dos serviços em:

    Patient Service: http://localhost:6543 ou 
    User Service: http://localhost:6544

## 7. Gerenciamento do Banco de Dados com nuvie-db

Uma decisão chave de arquitetura foi desacoplar a camada de persistência em um repositório dedicado, nuvie-db. Isso traz vantagens significativas:

- Fonte Única da Verdade: Todos os modelos e migrações estão em um só lugar.
- Automação: As migrações são automatizadas por schema do PostgreSQL, garantindo que cada microsserviço opere em seu domínio de dados isolado.
- Consistência: Facilita a manutenção da consistência do banco de dados em diferentes ambientes (desenvolvimento, teste, produção).

## 8. Próximos Passos e Melhorias Futuras

Embora a solução atual seja robusta, há espaço para evoluções que a tornariam pronta para um ambiente de produção em larga escala:

- Testes Automatizados: Implementar uma suíte de testes unitários e de integração para garantir a qualidade e a confiabilidade do código.
- Mecanismo de Busca Avançada: Pode-se integrar todos os dados mockados vindos da Synthea ao sumarizá-los com LLM e inserir em um banco vetorial. Dessa forma a consulta poderia ser feita de uma maneira dinâmica com linguagem natural (essa abordagem não foi feita por conta do tempo)
