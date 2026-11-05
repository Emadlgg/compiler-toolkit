"""Frame descriptors for ABI-verified external MIPS procedures.

External bodies are never lowered to TAC. Their declared frame sizes are
needed only to allocate the callee's activation record at call sites.
"""
from compiscript.activation_record import ActivationRecord
from .compiled_imports import CompiledImportError


def external_records(plan):
    records = {}
    for dep in plan.libraries:
        for name, item in dep.metadata['exports'].items():
            if item['kind'] == 'class':
                callables = item['methods'].values()
            elif item['kind'] == 'function':
                callables = [item]
            else:
                continue
            for method in callables:
                label = method['label']
                size = method['frame_size']
                if label in records:
                    if records[label].size != size:
                        raise CompiledImportError(f'ABI inconsistente para {label}')
                    continue
                record = ActivationRecord(label, 0)
                record.symbols_end = size
                records[label] = record
    return list(records.values())
