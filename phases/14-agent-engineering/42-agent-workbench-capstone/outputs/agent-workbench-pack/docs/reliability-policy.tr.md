# Reliability Policy

Workbench, sektörde tekrarlayan beş failure mode'unu absorbe eder:

1. Hallucinated action — kural seti + verification gate ile yakalanır.
2. Scope creep — scope kontratı diff check'i ile yakalanır.
3. Cascading errors — feedback kayıtları + refuse-on-null-exit ile yakalanır.
4. Context loss — repo memory tarafından absorbe edilir; chat source of truth değildir.
5. Tool misuse — reviewer rubric'in verification boyutu tarafından yakalanır.

Politika verification gate tarafından zorlanır. Override yolu imzalı
ve denetlenir; agent'ler kendilerini override edemez.
