import importlib, traceback, sys
print('CWD:', sys.path[0])
importlib.invalidate_caches()

try:
    from src.ingesta.loader import DataLoader
    print('LOADER OK')
except Exception:
    traceback.print_exc()

print('\n-- sys.modules before feature import --')
for k in ('src', 'src.ingesta', 'src.preprocessing', 'src.preprocessing.feature_engineering'):
    present = k in sys.modules
    m = sys.modules.get(k)
    print(k, present, getattr(m, '__file__', None))

try:
    fe = importlib.import_module('src.preprocessing.feature_engineering')
    print('\nFE OK:', hasattr(fe, 'generate_features'), getattr(fe, '__file__', None))
    print('FE dir keys (sample):', [n for n in dir(fe) if 'generate' in n or 'WINDOW' in n][:20])
except Exception:
    traceback.print_exc()

print('\n-- sys.modules after feature import --')
for k in ('src', 'src.ingesta', 'src.preprocessing', 'src.preprocessing.feature_engineering'):
    present = k in sys.modules
    m = sys.modules.get(k)
    print(k, present, getattr(m, '__file__', None))
