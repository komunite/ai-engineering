# Capstone 06 — Kubernetes için DevOps Troubleshooting Agent'ı

> AWS'in DevOps Agent'ı GA oldu, Resolve AI K8s playbook'larını yayınladı, NeuBird semantic monitoring'i demo ettirdi ve Metoro AI SRE'yi per-service SLO'lara bağladı. Üretim şekli oturdu: bir alert webhook ateşlenir, bir agent telemetri okur, K8s nesnelerinin bir graph'ında yürür, root-cause hipotezleri sıralar ve onay butonlu bir Slack brief'i post eder. Default'ta read-only. Her remediation bir insan tarafından kapılır. Bu capstone o agent, 20 sentetik incident üzerinde değerlendirilmiş ve üç paylaşılan case'de AWS'in Agent'ına karşı karşılaştırılmış.

**Tür:** Bitirme
**Diller:** Python (agent), TypeScript (Slack entegrasyonu)
**Ön koşullar:** Faz 11 (LLM engineering), Faz 13 (tools ve MCP), Faz 14 (agent'lar), Faz 15 (otonom), Faz 17 (infrastructure), Faz 18 (safety)
**Egzersize edilen fazlar:** P11 · P13 · P14 · P15 · P17 · P18
**Süre:** 30 saat

## Sorun

2025-2026 SRE anlatısı şu hale geldi: "AI agent'ları incident'leri triage eder, insanlar remediation'ları onaylar." AWS DevOps Agent, Resolve AI, NeuBird, Metoro, PagerDuty AIOps — hepsi üretimde bu şekli yayınlıyor. Agent Prometheus metrik'lerini, Loki log'larını, Tempo trace'leri, kube-state-metrics'i ve bir K8s nesneleri knowledge graph'ını okur. Beş dakika altında telemetri citation'larıyla sıralı bir root-cause hipotezi üretir. Slack üzerinden açık insan onayı olmadan asla yıkıcı komutlar yürütmez.

Zor işin çoğu reasoning değil, scoping ve safety. Agent'ın read-only-default bir RBAC yüzeyine, sertleştirilmiş bir MCP tool sunucusuna ve her komutun considered vs executed audit log'larına ihtiyacı var. Derinliğinin dışına çıktığını bilmeli ve escalate etmeli. Ve yeterince ucuz çalışmalı ki OOM-kill cascade'leri $5k'lık bir agent faturası üretmesin.

## Kavram

Agent bir knowledge graph üzerinde çalışır. Node'lar K8s nesneleri (Pod'lar, Deployment'lar, Service'ler, Node'lar, HPA'lar, PVC'ler) artı telemetri kaynakları (Prometheus series'leri, Loki stream'leri, Tempo trace'leri). Kenarlar ownership (Pod -> ReplicaSet -> Deployment), scheduling (Pod -> Node) ve observation (Pod -> Prometheus series) encode eder. Graph kube-state-metrics sync'i tarafından taze tutulur ve her alert'te yeniden örneklenir.

Bir alert ateşlendiğinde, agent etkilenen nesneden root-cause yapar. Kenarları yürür, ilgili telemetri dilimlerini çeker (son 15 dakika) ve bir hipotez taslağı çizer. Hipotez evidence ile sıralanır: kaç telemetri citation'ı destekliyor, ne kadar yeni, ne kadar spesifik. Top-3 hipotez graph-path görselleştirmeleri ve remediation aksiyonları için onay butonlarıyla Slack'e gider.

Remediation kapılı. İzin verilen default aksiyonlar read-only. Yıkıcı aksiyonlar (scale down, rollback, Pod silme) Slack onayı gerektirir; ArgoCD rollback hook'ları agent'ın asla tutmadığı bir auth token gerektirir. Audit log agent'ın *düşündüğü* her komutu kaydeder — sadece yürütülenleri değil — bu yüzden inceleme süreci near-miss'leri yakalar.

## Mimari

```
PagerDuty / Alertmanager webhook
           |
           v
     FastAPI receiver
           |
           v
   LangGraph root-cause agent'ı
           |
           +---- read-only MCP tool'ları ----+
           |                             |
           v                             v
   K8s knowledge graph              telemetri dilimleri
     (Neo4j / kuzu)              Prometheus, Loki, Tempo
   ownership + scheduling          son 15m, scoped
           |
           v
   hipotez sıralama (evidence ağırlığı)
           |
           v
   Slack brief + onay butonları
           |
           v (onaylandı)
   ArgoCD rollback hook / PagerDuty escalate
           |
           v
   audit log: considered vs executed, her komut
```

## Stack

- Observability kaynakları: Prometheus, Loki, Tempo, kube-state-metrics
- Knowledge graph: K8s nesneleri + telemetri kenarlarının Neo4j'i (managed) veya kuzu'su (embedded)
- Agent: per-tool allow-list'li, default'ta read-only LangGraph
- Tool transport: StreamableHTTP üzerinden FastMCP; yıkıcı tool'lar için approval gate arkasında ayrı sunucu
- Modeller: root-cause akıl yürütme için Claude Sonnet 4.7, log özetlemesi için Gemini 2.5 Flash
- Remediation: ArgoCD rollback webhook, PagerDuty escalate, Slack onay kartı
- Audit: append-only yapılı log (considered, executed, approved, outcome)
- Deployment: kendi dar RBAC role'ü olan K8s deployment'ı; ayrı namespace

## İnşa Et

1. **Graph ingestion.** kube-state-metrics'i her 30s'de bir Neo4j/kuzu'ya sync et. Node'lar: Pod, Deployment, Node, Service, PVC, HPA. Kenarlar: OWNED_BY, SCHEDULED_ON, EXPOSES, MOUNTS, SCALES. Telemetri overlay kenarları: OBSERVED_BY (bir Pod bir Prometheus series tarafından gözlenir).

2. **Alert receiver.** PagerDuty veya Alertmanager webhook'larını kabul eden FastAPI endpoint'i. Etkilenen nesne(ler)i ve SLO ihlalini çıkar.

3. **Read-only tool yüzeyi.** FastMCP üzerinden kubectl, Prometheus query, Loki logql, Tempo traceql'i wrap'le. Her tool dar bir RBAC verb'üne sahip ("get", "list", "describe"). Default sunucuda "delete", "exec", "scale" yok.

4. **Root-cause agent'ı.** Üç node'lu LangGraph: `sample` son-15-dakika telemetri dilimini çeker, `walk` graph'ı komşu nesneler için sorgular, `hypothesize` telemetri citation'larıyla sıralı root-cause adaylarının taslağını çizer.

5. **Evidence skorlama.** Her hipotezin bir skoru = recency * specificity * graph-path uzunluğu inverse * citation sayısı. Top-3 döndür.

6. **Slack brief.** Hipotez, graph-path görselleştirmesi (sunucu-tarafında render edilmiş bir alt-graph görüntüsü) ve en fazla bir remediation aksiyonu için onay butonlarıyla bir attachment post et.

7. **Remediation gate.** Yıkıcı tool'lar (scale down, rollback, delete) onay token'ı arkasında ikinci bir MCP sunucusunda yaşar. Agent onları ancak Slack kartı bir insan tarafından onaylandıktan sonra çağırabilir.

8. **Audit log.** Append-only JSONL: her aday komut için considered olup olmadığını, executed olup olmadığını, kimin onayladığını logla. Günlük S3'e gönder.

9. **Sentetik incident suite'i.** 20 senaryo inşa et: OOMKill cascade, DNS flap, HPA thrash, PVC fill, gürültülü komşu, hatalı sidecar, kötü ConfigMap rollout'u, certificate rotation, image-pull backoff, vs. Agent'ı root-cause doğruluğu ve hipoteze geçen süre üzerinde skorla.

## Kullan

```
webhook: alert.pagerduty.com -> checkout-api SLO ihlali, error oranı %14
[graph]   etkilenen: Deployment checkout-api (3 Pod, Node ip-10-2-3-4)
[walk]    komşular: ReplicaSet checkout-api-abc, Service checkout-api,
           son rollout 14m önce
[sample]  prometheus error_rate %14, yükseliş eğilimi; loki /api/v2/pay'de 500'ler
[hypo]    #1 kötü rollout: son image checkout-api:v2.41 /healthz'da başarısız
          citation'lar: deploy.yaml (rev 42), prometheus errorRate, loki 500 stack
[slack]   [v2.40'a ROLL BACK]  [ESCALATE]  [IGNORE]
          (onay gerekli; agent tek başına roll back yapmaz)
```

## Yayınla

Teslimat `outputs/skill-devops-agent.md`. Bir K8s cluster'ı ve alert kaynağı verildiğinde, agent sıralı root-cause hipotezleri ve Slack-kapılı bir remediation akışı üretir.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | Senaryo suite'inde RCA doğruluğu | 20 sentetik incident boyunca ≥%80 doğru root cause |
| 20 | Safety | Yıkıcı-aksiyon guard'ı audit log'da Slack onayı olmadan asla ateşlenmez |
| 20 | Hipoteze geçen süre | Alert'ten Slack brief'e p50 5 dakika altı |
| 20 | Açıklanabilirlik | Her hipotezin graph path'leri ve telemetri citation'ları var |
| 15 | Entegrasyon eksiksizliği | PagerDuty, Slack, ArgoCD, Prometheus uçtan uca çalışıyor |
| **100** | | |

## Alıştırmalar

1. AWS'in DevOps Agent'ının demo edildiği aynı üç incident üzerinde agent'ını çalıştır. Yan yana yayınla. Agent'ın nerede ayrıldığını raporla.

2. Onay olmadan yıkıcı olacak agent'ın *düşündüğü* herhangi bir komutu flag'leyen bir "near-miss" denetimi ekle. Bir hafta boyunca near-miss oranını ölç.

3. Hipotez modelini Claude Sonnet 4.7'den self-hosted Llama 3.3 70B'ye değiştir. RCA doğruluğu delta'sını ve incident başına dolar'ı ölç.

4. Causal filter inşa et: korele telemetri spike'larını gerçek bir root cause'dan ayır. 20-senaryo etiketlerinde küçük bir sınıflandırıcı eğit.

5. Bir rollback dry-run ekle: aynı manifest'li staging cluster'ına karşı ArgoCD rollback. Slack onay butonundan önce rollback planını canlı bir cluster'da doğrula.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| K8s knowledge graph | "Cluster graph'ı" | Node'lar = K8s nesneleri + telemetri series; kenarlar = ownership, scheduling, observation |
| Read-only-default | "Scoped RBAC" | Agent'ın service account'u sadece get/list/describe verb'lerine sahip; yıkıcı verb'ler onay arkasında ayrı sunucuda yaşar |
| Audit log | "Considered vs executed" | Her aday komutun, çalışıp çalışmadığının, kimin onayladığının append-only kaydı |
| Hipotez sıralama | "Evidence skoru" | Recency × specificity × graph-path uzunluğu inverse × citation sayısı |
| Slack onay kartı | "HITL gate" | Remediation butonlu interaktif Slack mesajı; bir insan tıklayana kadar agent ilerleyemez |
| Telemetri citation'ı | "Evidence pointer'ı" | Bir iddiayı destekleyen bir Prometheus query, Loki selector veya Tempo trace URL'i |
| MTTR | "Çözüme geçen süre" | Alert ateşlenmesinden SLO iyileşmesine kadar wall-clock |

## İleri Okuma

- [AWS DevOps Agent GA](https://aws.amazon.com/blogs/aws/aws-devops-agent-helps-you-accelerate-incident-response-and-improve-system-reliability-preview/) — kanonik 2026 referansı
- [Resolve AI K8s troubleshooting](https://resolve.ai/blog/kubernetes-troubleshooting-in-resolve-ai) — rakip referansı
- [NeuBird semantic monitoring](https://www.neubird.ai) — semantic-graph yaklaşımı
- [Metoro AI SRE](https://metoro.io) — SLO-öncelikli üretim çerçevesi
- [kube-state-metrics](https://github.com/kubernetes/kube-state-metrics) — cluster-state kaynağı
- [LangGraph](https://langchain-ai.github.io/langgraph/) — referans agent orkestratörü
- [FastMCP](https://github.com/jlowin/fastmcp) — Python MCP sunucusu framework'ü
- [ArgoCD rollback](https://argo-cd.readthedocs.io/en/stable/user-guide/commands/argocd_app_rollback/) — kapılı remediation hedefi
