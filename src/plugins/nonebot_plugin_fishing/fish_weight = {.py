import random
fish_weight = {
    "普通": {
        "weight": 100,
        "price_mpr": 0.1,
        "long": (1, 30),
    },
    "腐烂": {
        "weight": 20,
        "price_mpr": 0.05,
        "long": (15, 45),
    },
    "发霉": {
        "weight": 15,
        "price_mpr": 0.08,
        "long": (20, 150),
    },
    "金": {
        "weight": 5,
        "price_mpr": 0.15,
        "long": (125, 800),
    },
    "虚空": {
        "weight": 3,
        "price_mpr": 0.2,
        "long": (800, 4000),
    },
    "隐火": {
        "weight": 1,
        "price_mpr": 0.2,
        "long": (1000, 4000),
    }
}
quality = random.choice(list(fish_weight.keys()))
fish_quality_weight = [fish_weight[key]["weight"] for key in fish_weight]
result = random.choices(list(fish_weight.keys()),
                        weights=fish_quality_weight)[0]
print(result)
