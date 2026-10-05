# ادامهٔ پروژهٔ گرین — وضعیت و نقشهٔ ادامه

> سند انتقال دانش برای ادامهٔ توسعه در گفت‌وگوهای بعدی — اکتبر ۲۰۲۶

## ۱. هدف

گرین سامانه‌ای برای اثبات و پژوهش ریاضی با تمرکز اولیه بر حساب پئانو و نظریهٔ اعداد است. هدف بلندمدت فقط اثبات قضایای داده‌شده نیست؛ هدف ساخت چرخه‌ای است که ایدهٔ ریاضی تولید کند، آن را رسمی بررسی و اثبات کند، ارزش پژوهشی آن را ارزیابی کند و نتایج را برای نسل‌های بعد به کار گیرد.

ملاکت به عنوان لایهٔ تکاملی اضافه شده تا منابع محدود، رقابت، بقا، تبار، انتخاب و توازن اکتشاف/بهره‌برداری را مدل کند. درستی ریاضی هرگز توسط ملاکت یا مدل زبانی تعیین نمی‌شود.

## ۲. معماری فعلی

```text
AI / Idea Generator
        ↓
Candidate conjectures (untrusted)
        ↓
GAREEN
sample filter → research-value assessment → proof orchestration → formal verification
        ↓
Verified mathematical objects only
        ↓
MELAKAT
energy/resources → competition → survival → parent selection
        ↓
Selected parents
        ↓
AI / next generation
        ↺
```

مسئولیت‌ها:

- **مدل زبانی:** تولید ایده و conjecture؛ مرجع حقیقت نیست.
- **گرین:** نمایش و معنای ریاضی، فیلتر نمونه‌ای، research value، proof orchestration و verification.
- **Lean و موتورهای رسمی:** مرجع نهایی اعتبار اثبات در مسیر رسمی.
- **ملاکت:** جمعیت، انرژی، منابع، رقابت، مرگ، بقا، lineage و انتخاب والد.
- **Research Agent:** کنترل چرخهٔ والد → AI → گرین → verified → ملاکت → handoff.

## ۳. وضعیت گرین

گرین از prover ساده به proof orchestrator حرکت کرده است. آزمایش‌های قبلی نشان دادند اتصال ناقص به تاکتیک‌های اکوسیستم توان واقعی آنها را پنهان کرده بود. پس از اصلاح integration، ابزارهایی مانند `grind`، `aesop`، `omega`، `norm_num`، `linarith`، `nlinarith`، `exact?`، `apply?` و `lean-auto` بهتر استفاده شدند.

نتیجهٔ مهم: ارزش اثبات‌شدهٔ فعلی گرین بیشتر در orchestration، انتخاب استراتژی، adaptation به context و verification است؛ نه در ادعای برتری prover داخلی بر ابزارهای استاندارد.

## ۴. نتایج چندنسلی

| مرحله | کاندیدا | عبور نمونه | اثبات‌شده | Research accepted | خروجی ملاکت |
|---|---:|---:|---:|---:|---|
| نسل آغازین | 100 | 90 | 86 | 94 | مبنای جمعیت |
| نسل ۲ | 400 | 320 | 235 | 400 | 20 والد |
| نسل ۳ | 400 | 320 | 310 | 400 | 20 والد |
| نسل ۴ | 400 | 320 | 295 | 400 | 20 والد |
| نسل ۵ با API | 400 خام → 171 یکتا | 153 | 125 | 156 | 20 والد نسل ۶ |

فشار انتخاب ملاکت واقعاً population را تغییر داد. در چرخهٔ API، ۱۲۵ theorem تأییدشده وارد ملاکت شدند؛ میانگین research value حدود 40.4 بود و ۲۰ والد نهایی همگی score برابر 43 داشتند.

اما این هنوز به معنی افزایش عمق ریاضی نیست. بسیاری از گزاره‌های امتیازبالا transformations نزدیک به روابط ساده‌اند؛ مانند افزودن Successor، ضرب در یک یا قرار دادن دو طرف equality در context مشابه.

**نتیجهٔ کلیدی:** ملاکت خط‌کش فعلی ما را خوب اجرا می‌کند، ولی خود خط‌کش هنوز تعریف کافی از «ریاضی ارزشمند» ندارد.

## ۵. مشکل تابع ارزش

تابع research value فعلی می‌تواند complexity نحوی را بیش از حد پاداش دهد. بنابراین formula bloat ممکن است با depth ریاضی اشتباه شود.

نسخهٔ بعدی باید دست‌کم این مؤلفه‌ها را جداگانه بسنجد:

- novelty نسبت به knowledge base و جمعیت جاری؛
- derivational distance از والد و نتایج شناخته‌شده؛
- reuse potential به عنوان lemma؛
- structural richness بدون پاداش دادن به wrapperهای بی‌معنا؛
- proof difficulty؛
- diversity و فاصله از lineage غالب؛
- potential بلندمدت.

## ۶. خطر همگرایی زودرس

در آزمایش اخیر `distinct_lineages = 1` شد و خانوادهٔ جابجایی جمع غالب شد. این هشدار premature convergence است.

Selection نباید فقط بالاترین scalar score را نگه دارد. برای پژوهش ریاضی احتمالاً نیاز داریم:

```text
quality + novelty + diversity + potential
```

یک شاخه با score فعلی کمتر ممکن است به دلیل تفاوت ساختاری و پتانسیل آینده ارزش حفظ شدن داشته باشد. ملاکت باید بتواند niche، dormancy، reactivation و چند lineage را حفظ کند.

## ۷. Research Agent v1 — چرخهٔ ۵→۶

Branch:

```text
experiment/research-agent-v1-cycle-5-6
```

چرخهٔ کامل:

```text
20 parents
 → 20 sequential API calls
 → 400 syntactically valid outputs
 → global deduplication
 → 171 unique conjectures
 → 153 sample-pass
 → Gareen proof/verification
 → 125 verified
 → Melakat
 → 20 generation-6 parents
 → STOP
```

مصرف ثبت‌شده:

- API calls: **20**
- Input tokens: **5,106**
- Output tokens: **40,216**
- Total tokens: **45,322**

هزینهٔ دلاری از token count به تنهایی قابل تعیین نیست؛ باید در OpenAI Usage/Costs بررسی شود، زیرا حساب در برنامهٔ complimentary tokens ثبت شده بود.

Run کلیدی:

```text
37298008873
```

چرخه موفق شد و عمداً پس از handoff نسل ۶ متوقف شد.

## ۸. Audit Research Agent v1

### نکات مثبت

- چرخهٔ AI → گرین → ملاکت بدون دخالت دستی کامل شد.
- مدل فقط conjecture تولید کرد و truth authority نبود.
- همهٔ ۴۰۰ خروجی اولیه syntax معتبر داشتند.
- گرین فقط ۱۲۵ verified result را به ملاکت فرستاد.
- response IDs، token usage و artifact ثبت شدند.
- ملاکت ۲۰ والد نسل بعد را انتخاب کرد.

### مشکلات

- ۲۰ API call به صورت sequential بودند و latency غیرضروری ایجاد کردند.
- از ۴۰۰ خروجی فقط ۱۷۱ یکتا بود؛ **۲۲۹ خروجی، حدود ۵۷٪، تکراری بود.**
- 40,216 output token برای این مقدار novelty زیاد است.
- generator هنوز به transformations نزدیک به والد گرایش دارد.
- research value هنوز formula bloat را بیش از حد پاداش می‌دهد.
- diversity lineage فروپاشیده است.
- ملاکت داخل runner گرین checkout و اجرا شد؛ بنابراین GitHub Actions جداگانه‌ای در repository ملاکت دیده نمی‌شود. مسیر محاسباتی end-to-end است ولی observability باید بهتر شود.

## ۹. آیا ملاکت واقعاً ارزش افزوده دارد؟

هنوز ثابت نشده است.

اگر ملاکت فقط:

```text
score بالا → keep
score پایین → discard
```

انجام دهد، یک sort ساده در گرین تقریباً همان کار را می‌کند.

ملاکت زمانی ارزش واقعی دارد که ranking ساده قادر به آن نباشد:

- finite resources؛
- lineage competition؛
- diversity preservation؛
- multiple mathematical niches؛
- exploration vs exploitation؛
- dormancy/reactivation؛
- speciation؛
- long-term research budget allocation.

بنابراین باید آزمایش کنترل‌شدهٔ **گرین تنها در برابر گرین + ملاکت** انجام شود.

## ۱۰. آزمایش A/B پیشنهادی

دو سیستم باید دقیقاً generator، seed، proof budget و تعداد candidate یکسان داشته باشند:

```text
A: Generator → Gareen → ranking → next parents
B: Generator → Gareen → Melakat → next parents
```

معیارهای مقایسه:

- novelty؛
- diversity؛
- derivational distance؛
- reuse potential؛
- proof difficulty؛
- تعداد نتایج nontrivial؛
- lineage diversity؛
- token/compute cost به ازای نتیجهٔ مفید.

فقط اگر B تحت بودجهٔ برابر مزیت قابل اندازه‌گیری نشان دهد، می‌توانیم ادعا کنیم ملاکت ارزش علمی افزوده دارد.

## ۱۱. گام بعدی پیشنهادی

1. فعلاً نسل‌های بیشتری کورکورانه اجرا نشوند.
2. research-value metric اصلاح شود: anti-bloat، novelty، derivational distance، reuse potential و structural significance.
3. selection ملاکت برای حفظ چند lineage و niche اصلاح شود.
4. baseline بدون ملاکت ساخته شود.
5. A/B کنترل‌شده با بودجهٔ یکسان اجرا شود.
6. Research Agent به batching تغییر کند؛ به جای ۲۰ call sequential از تعداد کمی batch استفاده شود.
7. hard token/cost budget اضافه شود.
8. global novelty context و deduplication بهتر شود.
9. زمان API generation، dedup، Gareen proof و Melakat selection جداگانه ثبت شود.
10. Usage/Costs برای Run 45,322-token بررسی شود.
11. فقط پس از این audit، اجرای ۵ یا ۱۰ نسل خودکار انجام شود.
12. سپس دربارهٔ multi-agent researcher architecture تصمیم‌گیری شود.

## ۱۲. شاخه‌ها و Runهای کلیدی

- Gareen experiment: `experiment/ai-parent-conjectures-100`
- Research Agent v1: `experiment/research-agent-v1-cycle-5-6`
- Melakat integration: `experiment/gareen-chatgpt-five-generations`
- OpenAI smoke branch: `experiment/openai-api-smoke`
- Initial 100 conjectures: Run `37251144064`
- Generation 2: Run `37271437984`
- Generation 3: Run `37281762429`
- Generation 4: Run `37283561721`
- Research Agent 5→6: Run `37298008873`

## ۱۳. اصول غیرقابل‌مذاکره برای ادامه

1. AI خلاق است، نه مرجع حقیقت.
2. فقط نتایج formally verified وارد knowledge/evolution شوند.
3. «unproved» با CI/infrastructure failure یکی نیست.
4. تعداد theorem به تنهایی معیار پیشرفت نیست.
5. formula bloat نباید به عنوان research depth پاداش بگیرد.
6. branchهای آزمایشی تا زمان validation از مسیر اصلی جدا بمانند.
7. هزینه و compute budget باید محدود و قابل audit باشد.
8. provenance هر theorem و parent/lineage آن حفظ شود.

## ۱۴. سؤال محوری مرحلهٔ بعد

اکنون ثابت کرده‌ایم که می‌توانیم نسل‌های بیشتری بسازیم. سؤال بعدی این نیست که «آیا چرخه اجرا می‌شود؟».

سؤال علمی اصلی این است:

> **آیا تحت بودجهٔ برابر، چرخهٔ گرین + ملاکت واقعاً ما را به ریاضیات جدیدتر، متنوع‌تر و عمیق‌تر از گرینِ تنها می‌رساند؟**

پاسخ به این سؤال باید قبل از scale-up یا طراحی معماری multi-agent بعدی به دست آید.
