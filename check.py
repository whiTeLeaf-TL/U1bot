import pstats


p = pstats.Stats("result.out")
# 按照运行时间和函数名进行排序
# p.strip_dirs().sort_stats("cumulative", "name").print_stats(0.5)
p.strip_dirs().sort_stats("cumulative").print_stats(30)
