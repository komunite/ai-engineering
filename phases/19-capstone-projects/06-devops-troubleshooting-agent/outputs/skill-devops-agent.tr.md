---
name: devops-agent
description: Cluster knowledge graph'ı dolaşan, root cause sıralayan ve her remediation'ı Slack üzerinden gate'leyen bir Kubernetes troubleshooting agent'ı kur.
version: 1.0.0
phase: 19
lesson: 06
tags: [capstone, devops, sre, kubernetes, langgraph, fastmcp, aiops]
---

Bir K8s cluster ve bir alarm kaynağı (PagerDuty veya Alertmanager) verildiğinde, beş dakikadan kısa sürede sıralanmış root-cause hipotezleri üreten ve her remediation'ı Slack approval card üzerinden gate'leyen bir agent kur.

Build planı:

1. kube-state-metrics'i her 30s'de bir Neo4j veya kuzu içine ingest et. Pod, Deployment, Service, Node, PVC, HPA'ların grafiğini artı Prometheus, Loki ve Tempo kaynaklarına telemetry-overlay edge'lerini kur.
2. PagerDuty ve Alertmanager için bir FastAPI webhook receiver ayağa kaldır.
3. StreamableHTTP transport ile FastMCP üzerinden read-only tool'ları yay: kubectl get/describe, promql, logql, traceql.
4. Üç node'lu bir LangGraph root-cause agent kur: `sample` (15dk telemetry çek), `walk` (graph komşularını gez), `hypothesize` (adayları recency × specificity × citation count'a göre sırala).
5. Slack'e graph-path görselleştirmesi ile top-3 sıralanmış hipotezi approval butonlarıyla post et.
6. Destructive tool'ları (scale, rollback, delete) yalnızca Slack signoff sonrası agent'in elde ettiği approval token arkasında ayrı bir FastMCP server'a koy.
7. Append-only audit log tut: değerlendirilen her komut, onaylanıp onaylanmadığı, yürütülüp yürütülmediği, kimin onayladığı.
8. 20 sentetik incident senaryosu kur (OOMKill, DNS flap, HPA thrash, PVC fill, noisy neighbor, faulty sidecar, ConfigMap bad rollout, cert rotation, image-pull backoff, probe failure ve 10 tane daha). Agent'i RCA doğruluğu ve time-to-hypothesis ile skorla.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | Senaryo suite üzerinde RCA doğruluğu | 20 sentetik incident'te en az %80 doğru root cause |
| 20 | Safety | Audit log'da Slack onayı olmadan destructive-action guard hiç tetiklenmez |
| 20 | Time-to-hypothesis | Alarmdan Slack özetine p50 5 dakika altı |
| 20 | Açıklanabilirlik | Her hipotezin graph path'leri ve telemetry citation'ları var |
| 15 | Entegrasyon tamlığı | PagerDuty, Slack, ArgoCD, Prometheus uçtan uca çalışır |

Sert ret durumları:

- Read-only ve destructive tool'ları karıştıran tek MCP server'lı agent'lar.
- Telemetry citation'ları olmadan üretilen herhangi bir RCA. Citation'sız hipotezler reddedilmeli.
- Yalnızca yürütmeleri kaydeden audit log'lar. Değerlendirilen her komutu kaydetmek zorunda.
- 20 senaryolu suite'te seed'lerle çalıştırılmadan yapılan doğruluk iddiaları.

Reddetme kuralları:

- İnsan on-caller'dan Slack onayı olmadan remediate etmeyi reddet. Hipotez aşikar olsa bile.
- `kubectl exec`, `kubectl port-forward` veya herhangi bir interaktif tool'u read-only MCP üzerinden yaymayı reddet. Bunlar etkide destructive'tir.
- Per-deployment approval card olmadan birden fazla deployment üzerinde batch-apply remediation yapmayı reddet.

Çıktı: FastAPI receiver, LangGraph agent, read-only ve destructive MCP server'ları, Slack entegrasyonu, 20 senaryolu test suite'i, üç paylaşılan incident üzerinde AWS DevOps Agent'a karşı yan yana karşılaştırma ve bir haftalık gözlem penceresinde agent'in değerlendirip de yürütmediği near-miss komutları üzerine bir yazımı içeren bir repo.
