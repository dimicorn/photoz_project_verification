# Источники

Каждая запись — с идентификатором и происхождением: откуда получены метаданные и откуда взято
утверждение (из аннотации или из прочитанного текста).

| № | Работа | OpenAlex | DOI | Что берём | Прочитано |
|---|---|---|---|---|---|
| 1 | Beck R. E., Lin C.-A. et al. On the realistic validation of photometric redshifts. MNRAS, 2017, 468(4): 4323–4339 | W2584691382 | 10.1093/mnras/stx687 | Каталог Happy (A/B/C/D), стандарт валидации photo-z; проблема неполного покрытия feature space спектроскопией | аннотация, 2026-10-18 |
| 2 | Ashmead F., Newman J. A. et al. Optimizing Photometric Redshift Training Sets. I. Efficient Compression of the Galaxy Color–Redshift Relation with UMAP. ApJ, 2026, 1010(2): 140 | W4417288889 | 10.3847/1538-4357/aea207 | UMAP-kNN-z: сжатие цветового пространства до многообразия, предсказание медианой z соседей; устойчивость к смещённой выборке | аннотация, 2026-10-18 |
| 3 | Salvato M., Ilbert O., Hoyle B. The many flavours of photometric redshifts. Nature Astronomy, 2018, 3: 212–222 | W2963284157 | 10.1038/s41550-018-0478-0 | Обзор методов photo-z: template fitting, ML, empirical; метрики качества (bias, σ_NMAD, outlier fraction) | аннотация, 2026-10-18 |
| 4 | Newman J. A., Gruen D. Photometric Redshifts for Next-Generation Surveys. ARA&A, 2022, 60: 363–414 | W4281645604 | 10.1146/annurev-astro-032122-014611 | Требования к photo-z для Rubin/Euclid/Roman; необходимость репрезентативных обучающих выборок | аннотация, 2026-10-18 |
| 5 | Brammer G. B., van Dokkum P. G., Coppi P. EAZY: A Fast, Public Photometric Redshift Code. ApJ, 2008, 686(2): 1503–1513 | W2080173214 | 10.1086/591786 | Template-fitting код EAZY; использование semianalytical моделей вместо biased spectroscopic samples | аннотация, 2026-10-18 |
| 6 | Lima M., Cunha C. E. et al. Estimating the redshift distribution of photometric galaxy samples. MNRAS, 2008, 390(1): 118–130 | W2145550174 | 10.1111/j.1365-2966.2008.13510.x | Метод nearest-neighbour weighting для оценки N(z); устойчивость в sparse regions | аннотация, 2026-10-18 |
| 7 | Rivera J. D., Moraes B. et al. Degradation analysis in the estimation of photometric redshifts from non-representative training sets. MNRAS, 2018, 477(4): 4330–4347 | W2796135634 | 10.1093/mnras/sty880 | Анализ деградации photo-z при non-representative training sets в magnitude space; обучение в colour space снижает ошибки | аннотация, 2026-10-18 |
| 8 | Leistedt B., Hogg D. W. Data-driven, Interpretable Photometric Redshifts Trained on Heterogeneous and Unrepresentative Data. ApJ, 2017, 838(1): 5 | W2560721689 | 10.3847/1538-4357/aa6332 | Gaussian processes в flux–redshift space; обучение на heterogeneous data без полного пространственного перекрытия | аннотация, 2026-10-18 |