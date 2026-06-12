# Plano de Implementação: Prévia de SLA por Período com Dados do Zabbix

> **Para agentes de execução:** SUB-SKILL OBRIGATÓRIA: usar `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa por tarefa. As etapas usam checklist com `- [ ]`.

**Objetivo:** Adicionar uma prévia de SLA baseada em eventos reais do Zabbix para um período informado, com foco em associação por `tag` e suporte opcional a `hostgroup`.

**Arquitetura:** A nova fatia reaproveita o catálogo persistido de serviços e as regras de SLA já salvas no banco. O backend resolve o serviço, consulta eventos do Zabbix conforme a origem configurada (`tag` ou `hostgroup`), consolida intervalos de indisponibilidade sem dupla contagem e aplica o cálculo puro de disponibilidade já existente no domínio.

**Stack:** FastAPI, SQLAlchemy, Pydantic, Pytest, biblioteca padrão Python para HTTP/JSON

---

## Estrutura de arquivos proposta

- `backend/app/infrastructure/zabbix/client.py`: cliente JSON-RPC com execução real e helpers mínimos de consulta
- `backend/app/application/sla/preview_zabbix_service_sla.py`: caso de uso da prévia de SLA por período usando Zabbix
- `backend/app/schemas/zabbix_sla_preview.py`: contratos HTTP da nova prévia
- `backend/app/api/v1/zabbix_sla_preview.py`: rota HTTP da apuração baseada em Zabbix
- `backend/app/main.py`: registro da nova rota
- `backend/tests/test_zabbix_client.py`: cobertura do cliente JSON-RPC
- `backend/tests/test_zabbix_sla_preview.py`: cobertura ponta a ponta da nova rota
- `README.md`: documentação do novo endpoint

## Tarefa 1: Fortalecer o cliente Zabbix

**Arquivos:**
- Modificar: `backend/app/infrastructure/zabbix/client.py`
- Modificar: `backend/tests/test_zabbix_client.py`

- [ ] **Passo 1: Escrever o teste falhando da chamada JSON-RPC**

```python
def test_zabbix_client_calls_transport_and_returns_result() -> None:
    calls: list[dict[str, object]] = []

    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        calls.append({"url": url, "payload": payload})
        return {"result": [{"eventid": "10"}]}
```

- [ ] **Passo 2: Rodar o teste para confirmar a falha**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_zabbix_client.py -q`
Esperado: FAIL por ausência do método de execução

- [ ] **Passo 3: Implementar execução JSON-RPC e helpers**

```python
def call(self, method: str, params: dict[str, object]) -> object:
    payload = self.build_request(method=method, params=params)
    ...
```

- [ ] **Passo 4: Rodar os testes do cliente**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_zabbix_client.py -q`
Esperado: PASS

## Tarefa 2: Caso de uso de prévia de SLA por período

**Arquivos:**
- Criar: `backend/app/application/sla/preview_zabbix_service_sla.py`
- Testar via: `backend/tests/test_zabbix_sla_preview.py`

- [ ] **Passo 1: Escrever o teste falhando do cálculo por tag**

```python
def test_preview_from_zabbix_tag_returns_availability_and_downtime():
    ...
    assert response.json()["data"]["downtime_minutes"] == 18
```

- [ ] **Passo 2: Rodar o teste para confirmar a falha**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_zabbix_sla_preview.py -q`
Esperado: FAIL por ausência do caso de uso e da rota

- [ ] **Passo 3: Implementar consolidação de intervalos**

```python
def _merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    ...
```

- [ ] **Passo 4: Rodar o teste da nova prévia**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_zabbix_sla_preview.py -q`
Esperado: PASS

## Tarefa 3: Expor a rota HTTP da prévia por período

**Arquivos:**
- Criar: `backend/app/schemas/zabbix_sla_preview.py`
- Criar: `backend/app/api/v1/zabbix_sla_preview.py`
- Modificar: `backend/app/main.py`

- [ ] **Passo 1: Criar contratos de request/response**

```python
class ZabbixSlaPreviewRequest(BaseModel):
    service_key: str
    period_start: datetime
    period_end: datetime
```

- [ ] **Passo 2: Registrar `POST /api/v1/sla/preview/zabbix`**

```python
router = APIRouter(prefix="/api/v1/sla", tags=["sla"])
```

- [ ] **Passo 3: Rodar os testes HTTP**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_zabbix_sla_preview.py tests/test_system_endpoints.py -q`
Esperado: PASS

## Tarefa 4: Regressão final e documentação

**Arquivos:**
- Modificar: `README.md`

- [ ] **Passo 1: Atualizar a documentação da fatia**

```markdown
- prévia de SLA por período usando eventos reais do Zabbix
- associação principal por tag com suporte a hostgroup
```

- [ ] **Passo 2: Rodar a suíte completa do backend**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider -q`
Esperado: PASS

- [ ] **Passo 3: Validar compose do backend**

Rodar: `docker compose -f docker-compose.backend.yml config`
Esperado: PASS

## Auto-revisão

- Cobertura do objetivo: este plano adiciona a primeira apuração com eventos reais do Zabbix, respeitando a estratégia híbrida com foco em trigger/tag e suporte a hostgroup.
- Limite intencional: ainda não cobre exclusão de manutenção planejada, exportação, histórico consolidado mensal salvo em banco ou agendamento.
- Consistência: a nova rota deve reaproveitar serviço persistido, regra ativa persistida e cálculo puro de SLA já existente para evitar lógica duplicada.
