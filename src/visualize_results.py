from pathlib import Path

import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint
import numpy as np
import pandas as pd



ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "reports" / "data"
output_dir = ROOT / "reports" / "figures"
output_dir.mkdir(parents=True, exist_ok=True)

# Результаты регрессий
results = pd.read_csv(DATA_DIR / "model_results.csv")

if set(results["model"]) != {"M0", "M1", "M2"}:
    raise ValueError("Ожидались результаты M0, M1 и M2")

if results["n"].nunique() != 1:
    raise ValueError("Модели построены на разных выборках")

results = (
    results.set_index("model")
    .loc[["M0", "M1", "M2"]]
    .reset_index()
)

results["model"] = results["model"].map({
    "M0": "M0: Unadjusted",
    "M1": "M1: Account age",
    "M2": "M2: Fully adjusted",
})

# Папка с графиками
output_dir = Path("reports/figures")
output_dir.mkdir(parents=True, exist_ok=True)

# Позиции моделей на оси Y
y = np.arange(len(results))

# Асимметричные доверительные интервалы
errors = np.array([
    results["or"] - results["ci_lower"],
    results["ci_upper"] - results["or"],
])

fig, ax = plt.subplots(figsize=(9, 4.5))

ax.errorbar(
    x=results["or"],
    y=y,
    xerr=errors,
    fmt="o",
    markersize=8,
    capsize=5,
    linewidth=2,
)

# Нулевая гипотеза: OR = 1
ax.axvline(
    1,
    linestyle="--",
    linewidth=1.5,
    alpha=0.7,
)

# Подписи моделей
ax.set_yticks(y)
ax.set_yticklabels(results["model"])
ax.invert_yaxis()

# Подписываем оценки справа
for i, row in results.iterrows():
    label = (
        f"{row['or']:.2f} "
        f"[{row['ci_lower']:.2f}, "
        f"{row['ci_upper']:.2f}]"
    )

    ax.text(
        1.82,
        i,
        label,
        va="center",
        fontsize=10,
    )

ax.set_xlim(0.9, 2.3)
ax.set_xlabel("Odds Ratio (95% CI)")
ax.set_title(
    "First Answer Matters?\n"
    "Association between early response and return"
)

ax.grid(axis="x", alpha=0.2)
ax.set_axisbelow(True)

fig.tight_layout()

# Сохраняем изображение
output_path = output_dir / "odds_ratios_2023.png"

fig.savefig(
    output_path,
    dpi=200,
    bbox_inches="tight",
)

plt.show()

print(f"Saved: {output_path}")

# Фактическая возвращаемость
retention = pd.read_csv(
    DATA_DIR / "retention_results.csv"
)

if set(retention["answered_24h"]) != {0, 1}:
    raise ValueError("Ожидались две группы пользователей")

retention = (
    retention.set_index("answered_24h")
    .loc[[0, 1]]
    .reset_index()
)

retention["group"] = retention["answered_24h"].map({
    0: "No answer within 24h",
    1: "Answered within 24h",
})

retention["rate"] = (
    retention["returned"] / retention["users"]
)

# 95% доверительные интервалы Уилсона
ci_lower, ci_upper = proportion_confint(
    count=retention["returned"],
    nobs=retention["users"],
    alpha=0.05,
    method="wilson",
)

retention["ci_lower"] = ci_lower
retention["ci_upper"] = ci_upper

# Асимметричные интервалы
errors = np.array([
    retention["rate"] - retention["ci_lower"],
    retention["ci_upper"] - retention["rate"],
]) * 100

fig, ax = plt.subplots(figsize=(8, 5))

bars = ax.bar(
    retention["group"],
    retention["rate"] * 100,
    yerr=errors,
    capsize=7,
    width=0.55,
    alpha=0.85,
)

# Подписи размещаем выше доверительных интервалов
for bar, row in zip(bars, retention.itertuples()):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        row.ci_upper * 100 + 0.35,
        f"{row.rate * 100:.2f}%",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
    )


# Показываем разницу между группами
difference_pp = (
    retention.loc[1, "rate"]
    - retention.loc[0, "rate"]
) * 100

ax.text(
    0.5,
    0.95,
    f"Observed difference: {difference_pp:+.2f} pp",
    transform=ax.transAxes,
    ha="center",
    va="top",
    fontsize=11,
)

ax.set_ylim(0, 18)
ax.set_ylabel("30-day return rate (%)")

ax.set_title(
    "First Answer Matters?\n"
    f"Return outside the first thread "
    f"(n = {retention['users'].sum():,})"
)

ax.grid(axis="y", alpha=0.2)
ax.set_axisbelow(True)

fig.tight_layout()

output_path = output_dir / "retention_by_answer_2023.png"

fig.savefig(
    output_path,
    dpi=200,
    bbox_inches="tight",
)

plt.show()

print(f"Saved: {output_path}")


# Анализ чувствительности к порогу ответа
# Скорректированные результаты M2 (n = 5140)

# Результаты анализа чувствительности
thresholds = pd.read_csv(
    DATA_DIR / "threshold_results.csv"
).sort_values("threshold_hours").reset_index(drop=True)

thresholds["threshold"] = (
    thresholds["threshold_hours"].astype(str)
    + " hours"
)

thresholds["difference"] = thresholds["difference_pp"]
thresholds["ci_lower"] = thresholds["ci_lower_pp"]
thresholds["ci_upper"] = thresholds["ci_upper_pp"]

y = np.arange(len(thresholds))

errors = np.array([
    thresholds["difference"] - thresholds["ci_lower"],
    thresholds["ci_upper"] - thresholds["difference"],
])

fig, ax = plt.subplots(figsize=(9, 4.5))

ax.errorbar(
    thresholds["difference"],
    y,
    xerr=errors,
    fmt="o",
    markersize=8,
    linewidth=2,
    capsize=5,
)

# Линия отсутствия различия
ax.axvline(
    0,
    linestyle="--",
    linewidth=1.5,
    alpha=0.7,
)

ax.set_yticks(y)
ax.set_yticklabels(thresholds["threshold"])
ax.invert_yaxis()

# Подписи результатов
for i, row in thresholds.iterrows():
    label = (
        f"+{row['difference']:.2f} pp "
        f"[{row['ci_lower']:.2f}, "
        f"{row['ci_upper']:.2f}]"
    )

    ax.text(
        6.0,
        i,
        label,
        va="center",
        fontsize=10,
    )

ax.set_xlim(-0.4, 8.6)

ax.set_xlabel(
    "Adjusted difference in return probability (pp)"
)

ax.set_title(
    "First Answer Matters?\n"
    "Sensitivity to the early-answer threshold"
)

ax.grid(axis="x", alpha=0.2)
ax.set_axisbelow(True)

fig.tight_layout()

output_path = (
    output_dir / "answer_threshold_sensitivity_2023.png"
)

fig.savefig(
    output_path,
    dpi=200,
    bbox_inches="tight",
)

plt.show()

print(f"Saved: {output_path}")