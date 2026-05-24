# Handoff Protocol

Her session şunları içeren bir handoff paketi ile biter:

- summary
- changed_files
- commands_run
- failed_attempts
- open_risks (severity + detail)
- next_action (somut bir adım)
- verdict_pointer (verification + review raporlarına yollar)

Paket hem handoff.md (insanlar) hem de handoff.json (sonraki agent) olarak gönderilir.
Eksik alanlar session-sonu hook'unu durdurur.
