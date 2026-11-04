"""Convencion Compiscript: marco reservado por llamador, fp = inicio.

fp+0 retorno; fp+4 ra; fp+8 fp anterior; fp+12 enlace estatico;
fp+16.. parametros, locales y temporales. Pila descendente.
"""


class FrameManager:
    HEADER = 16
    WORD = 4
    MAX_IMMEDIATE = 32767

    @staticmethod
    def frame_size(size):
        if not isinstance(size, int) or size < FrameManager.HEADER:
            raise ValueError('Tamano de marco invalido')
        return (size + 3) & ~3

    @staticmethod
    def validate_call(size, nargs):
        if nargs < 0:
            raise ValueError('Cantidad de argumentos negativa')
        if size < FrameManager.HEADER + nargs * FrameManager.WORD:
            raise ValueError('El marco no tiene espacio para los argumentos')

    @staticmethod
    def reserve(size):
        """Secuencia valida incluso si el desplazamiento excede 16 bits."""
        size = FrameManager.frame_size(size)
        if size <= FrameManager.MAX_IMMEDIATE:
            return [f'  addiu $sp, $sp, -{size}']
        return [f'  li $t8, {size}', '  subu $sp, $sp, $t8']

    @staticmethod
    def restore(size):
        size = FrameManager.frame_size(size)
        if size <= FrameManager.MAX_IMMEDIATE:
            return [f'  addiu $sp, $fp, {size}']
        return [f'  li $t8, {size}', '  addu $sp, $fp, $t8']
