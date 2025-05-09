from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import itertools


@dataclass
class Module:
    abstract: str
    concrete: str | dict[str, str]
    name: str

    def get_concrete(self, language: str) -> Optional[str]:
        if isinstance(self.concrete, dict):
            return self.concrete.get(language)
        return self.concrete


magma = Module('Magma', {'Eng': 'MagmaEng'}, 'Magma')
xml = Module('XmlMagma', {'Eng': 'XmlMagmaEng'}, 'X')
dollarmath = Module('DollarMath', 'DollarMathConcr', 'D')

testlex = Module('TestEngLex', {'Eng': 'TestEngLexConcr'}, 'LTen')

directory = Path(__file__).parent / 'combinations'


print('Delete old combinations')

for file in directory.glob('*.gf'):
    print(f'    Deleting {file}')
    file.unlink()

print('Generating new combinations')

extensions = [xml, dollarmath]
# lexica cannot be combined with other lexica
lexica = [None, testlex]

for n in range(1, len(extensions) + 1):
    for xcombo in itertools.combinations(extensions, n):
        for lex in lexica:
            if lex is not None:
                combo = list(xcombo) + [lex, magma]
            else:
                combo = list(xcombo) + [magma]
            name = ''.join(mod.name for mod in combo)

            combo = [magma] + combo[:-1]   # if magma is in front, we get an error (GF bug?)

            print(f'    Generating {name}')

            with open(directory / f'{name}.gf', 'w') as f:
                f.write(f'abstract {name} = ' + ', '.join(mod.abstract for mod in combo) + '\n')

            for lang in magma.concrete.keys():
                concretes = [mod.get_concrete(lang) for mod in combo]
                if all(concretes):
                    with open(directory / f'{name}{lang}.gf', 'w') as f:
                        f.write(f'concrete {name}{lang} of {name} = ' + ', '.join(concretes) + '\n')

