# Agent Rules

## startup/state-file-fresh
- category: startup
- check: state_file_fresh
Agent herhangi bir tool çağrısından önce agent_state.json'ı okumalı.

## forbidden/no-out-of-scope-writes
- category: forbidden
- check: no_out_of_scope_writes
Aktif görevin scope kontratının dışındaki bir dosyayı asla düzenleme.

## done/tests-pass
- category: definition_of_done
- check: tests_pass
Bir görev yalnızca her acceptance komutu sıfırla çıktığında done olur.

## uncertainty/open-question-note
- category: uncertainty
- check: opened_question_when_unsure
Güven eşiğin altındayken, tahmin yerine bir soru notu aç.

## approval/new-dependency
- category: approval
- check: new_dependency_approved
Bir runtime bağımlılığı eklemek açık insan onayı gerektirir.
