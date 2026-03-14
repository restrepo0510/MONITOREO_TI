import importlib, sys, inspect
print('CWD', sys.path[0])
importlib.invalidate_caches()

m = importlib.import_module('src.preprocessing.feature_engineering')
print('MODULE FILE:', getattr(m, '__file__', None))
print('MODULE TYPE:', type(m))
print('\nDIR KEYS COUNT:', len([k for k in dir(m)]))
print('DIR SAMPLE:', [k for k in dir(m)][:60])

print('\n__dict__ keys:')
for k in list(m.__dict__.keys()):
    print('-', k)

# Try to access generate_features
print('\nHas generate_features?', 'generate_features' in m.__dict__)
if 'generate_features' in m.__dict__:
    print('Is function?', inspect.isfunction(m.__dict__['generate_features']))
    print('Source (first 20 lines):')
    src = inspect.getsource(m.__dict__['generate_features'])
    print('\n'.join(src.splitlines()[:20]))
else:
    print('No generate_features in module dict; printing file content for debugging:')
    with open(m.__file__, 'r', encoding='utf-8') as f:
        content = f.read()
    print('--- FILE START ---')
    lines = content.splitlines()
    for i,l in enumerate(lines[:200], start=1):
        print(f'{i:03}: {l}')
    print('--- FILE END ---')
