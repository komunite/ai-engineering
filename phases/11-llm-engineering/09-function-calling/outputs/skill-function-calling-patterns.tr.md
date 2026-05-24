---
name: skill-function-calling-patterns
description: Production'da function calling implementasyonu için karar çerçevesi — tool tasarımı, hata işleme, güvenlik ve sağlayıcı pattern'leri
version: 1.0.0
phase: 11
lesson: 09
tags: [function-calling, tool-use, agents, mcp, security, openai, anthropic]
---

# Function Calling Pattern'leri

Tool kullanan bir LLM uygulaması kurarken, bu karar çerçevesini uygula.

## Function calling ne zaman kullan

**Function calling kullan:**
- Model gerçek zamanlı veriye ihtiyaç duyuyorsa (hava, hisse fiyatları, veritabanı sorguları)
- Görev yan etkiler gerektiriyorsa (e-posta gönderme, kayıt oluşturma, kod deploy etme)
- Model kullanıcı niyetine göre birden çok eylem arasında seçmeli
- Dış sistemlerle etkileşen bir agent kuruyorsan

**Yerine structured outputs kullan:**
- Metinden veri çıkarımı gerekiyorsa (dış çağrı gerekmez)
- Çıktı, ara adım değil nihai üründür
- Tek bir şeman var, seçilecek birden çok tool değil

**İkisini de kullan:**
- Model bir tool çağırır, sonra tool sonucunu belirli bir çıktı formatına yapılandırır

## Tool tasarım kılavuzu

1. **Bir tool, bir eylem.** Sorgu, ekleme, güncelleme ve silme işlemlerini yöneten `manage_database` adlı bir tool çok geniştir. `query_records`, `insert_record`, `update_record` olarak böl. Model spesifik tool'larla daha iyi seçer.

2. **Description'lar prompt'tur.** Model seçim için tool description'larını okur. Onları junior bir developer için talimat yazıyormuş gibi yaz. Sadece tool'un ne yaptığını değil, ne döndürdüğünü de dahil et.

3. **Enum'larla kısıtla.** Bir parametre 3-10 geçerli değere sahipse, enum kullan. Model string'ler icat eder — "celsius", "Celsius", "C", "metric" — kısıtlamazsan.

4. **Az tool daha iyi.** GPT-4o 5-10 tool'u iyi işler. 20+ tool'da seçim doğruluğu düşer. 50+ tool'da %10-15 yanlış tool seçimi bekle. İlgili işlevsellikleri grupla veya bir routing katmanı kullan.

5. **Required gerçekten required demektir.** Bir parametreyi sadece tool literally onsuz çalışamıyorsa required işaretle. İyi varsayılanları olan opsiyonel parametreler tool çağrı başarısızlıklarını azaltır.

## Sağlayıcıya özgü pattern'ler

### OpenAI (GPT-4o, o3, GPT-4o-mini)

```python
tools=[{"type": "function", "function": {"name": ..., "parameters": ...}}]
tool_choice="auto"       # model karar verir
tool_choice="required"   # en az bir tool çağırmalı
tool_choice={"type": "function", "function": {"name": "specific_tool"}}
```

- Paralel tool çağrılarını destekler (tek yanıtta birden çok `tool_calls`)
- Tool çağrı ID'leri sonuçlarla birlikte geri gönderilmeli
- `gpt-4o-mini` 10x daha ucuz ve basit tool routing'i iyi işler
- Structured outputs mode garantili şema uyumu için tool parametreleriyle çalışır

### Anthropic (Claude 3.5 Sonnet, Claude 4 Opus)

```python
tools=[{"name": ..., "description": ..., "input_schema": ...}]
tool_choice={"type": "auto"}     # model karar verir
tool_choice={"type": "any"}      # en az bir tool çağırmalı
tool_choice={"type": "tool", "name": "specific_tool"}
```

- Tool çağrıları `type: "tool_use"` content block'ları olarak görünür
- Sonuçlar `type: "tool_result"` ile user mesajlarına gider
- Alan adı `parameters` değil `input_schema` (yaygın migration bug'ı)
- Yanıt başına birden çok tool çağrısını destekler

### Google (Gemini 2.0 Flash, Gemini 2.0 Pro)

```python
function_declarations=[{"name": ..., "description": ..., "parameters": ...}]
function_calling_config={"mode": "AUTO"}   # veya "ANY" veya "NONE"
```

- Top-level'da `function_declarations` kullanır
- Sonuçlar `function_response` part'ları ile döndürülür
- Paralel function calling'i destekler

### Açık kaynak modeller (Llama 3, Hermes, Qwen)

- Standartlaştırılmış format yok — model ve serving framework'üne göre değişir
- Hermes formatı (NousResearch) en yaygın fine-tune'lanmış konvansiyon
- vLLM desteklenen modeller için OpenAI-uyumlu tool calling'i destekler
- Ollama uyumlu modellerle temel tool calling'i destekler
- Production'dan önce tool seçim doğruluğunu test et — açık modeller Berkeley Function Calling Leaderboard'da GPT-4o'dan %15-30 daha az doğrudur

## Hata işleme pattern'leri

### Yapılandırılmış hatalar döndür

```json
{"error": true, "message": "'Toky' şehri bulunamadı. 'Tokyo' demek mi istediniz?", "code": "NOT_FOUND", "suggestions": ["Tokyo"]}
```

Eylem alınabilir bilgi dahil et. "Bulunamadı" kötüdür. "Bulunamadı, X demek mi istediniz?" iyidir. Model hata mesajlarını kendini düzeltmek için kullanır.

### Retry stratejisi

1. Tool çağrısı düzeltilebilir bir hatayla başarısız olur (yazım hatası, yanlış enum değeri)
2. Hatayı tool sonucu olarak modele geri gönder
3. Model ayarlar ve yeniden dener
4. Tool çağrısı başına maksimum 3 retry
5. 3 başarısızlıktan sonra hatayı kullanıcıya döndür

### Timeout işleme

Tüm tool çalıştırmalarında timeout ayarla. 30 saniye makul bir varsayılan. Bir tool timeout olursa, modelin kullanıcıyı bilgilendirebilmesi için takılmak yerine yapılandırılmış bir timeout hatası döndür.

## Güvenlik checklist

| Kontrol | Neden | Nasıl |
|-------|-----|-----|
| Function'ları allowlist'le | Keyfi kod çalıştırmayı önle | Sadece kullanıcının ihtiyacı olan tool'ları kaydet |
| Argüman tiplerini doğrula | Tip karışıklığı saldırılarını önle | Çalıştırmadan önce tipleri kontrol et |
| String argümanları temizle | Injection'ı önle | Özel karakterleri reddet veya escape et |
| Veritabanı sorgularını parametrele | SQL injection'ı önle | Model üretilen SQL'i asla doğrudan geçme |
| Tool sonuçlarını filtrele | Veri sızıntısını önle | API key'leri, PII, iç hataları kaldır |
| Tool çağrılarını rate limit'le | Kaçak döngüleri önle | Konuşma başına maks 10-20 çağrı |
| Tüm tool çağrılarını logla | Audit trail | Tool adı, argümanlar, sonuç, timestamp sakla |
| Path traversal'ı engelle | Dosya sistemi erişimini önle | Dosya tool'larında `..` ve absolute path'leri reddet |
| Kod çalıştırmayı sandbox'la | Sistem erişimini önle | Container'lar veya kısıtlı builtin'ler kullan |
| Dönüş boyutunu doğrula | Context stuffing'i önle | 10KB üstü sonuçları kes |

## Performans optimizasyonu

- **Paralel çağrılar:** Model birden çok bağımsız tool istediğinde, `asyncio.gather()` veya `concurrent.futures` ile eşzamanlı çalıştır
- **Caching:** Aynı oturumda aynı argümanlar için tool sonuçlarını cache'le (hava 60 saniyede değişmez)
- **Streaming:** Tool sonuçları çekilirken modelin nihai yanıtını stream et
- **Tool budama:** Context dar ise, sadece mevcut sorguya alakalı tool tanımlarını dahil et (filtrelemek için sınıflandırıcı kullan)
- **Routing için küçük modeller:** Tool seçimi için `gpt-4o-mini` veya `claude-3-5-haiku` kullan, sonra sentez için daha güçlü bir modele sonuçları geçir

## Sık karşılaşılan failure pattern'leri

| Başarısızlık | Neden | Çözüm |
|---------|-------|-----|
| Yanlış tool seçildi | Muğlak description'lar | Description'ları spesifik tetikleyici kelimelerle yeniden yaz |
| Eksik required arg'lar | Model bir parametreyi unuttu | Parametre description'larına net örnekler ekle |
| Sonsuz tool döngüsü | Model aynı tool'u çağırmaya devam ediyor | Maks iterasyon ayarla (5-10) ve tekrar eden çağrıları tespit et |
| Halüsinasyonlu argümanlar | Model makul ama yanlış değerler icat eder | Enum kullan, bilinen değerlere karşı doğrula |
| Tool sonucu çok büyük | API 100KB veri döndürdü | Geri beslemeden önce kes veya özetle |
| Model tool sonucunu yok sayıyor | Sonuç formatı kafa karıştırıcı | Net alan adlarıyla temiz JSON döndür |
