# Quickstart

Requisitos: **Python ≥ 3.10** y Pillow (`pip install Pillow`).

Soporte: solo Band 9 (`DeviceType="366"`, 192×490). Detalle: [`STATUS.md`](STATUS.md).

## 1. Sonda mínima

```bash
cd miband9-face-packer
python make_minimal.py
python pack_face.py samples/minimal probe.face --id 123456789
python validate_gb.py probe.face
```

`validate_gb.py` debe reportar PASS. A partir de ahí, edita PNG en
`samples/minimal/images/` y coordenadas del `.fprj`.

## 2. Ejemplo verificado (byte-exact)

```bash
cd miband9-face-packer
python pack_face.py ../ejemplo-verificado salida.face --id 167210065
python inspect_face.py salida.face
```

`salida.face` debe coincidir con `ejemplo-verificado/AnalogFull.face`
(SHA-256 en [`STATUS.md`](STATUS.md)).

## 3. Suite de tests

```bash
cd miband9-face-packer
MINIMAL_ANALOG_DIR=../ejemplo-verificado python -m unittest discover -s .
```

## 4. Instalar en la banda

Fuera del compilador. Camino documentado: [Gadgetbridge](https://gadgetbridge.org/)
→ Dispositivo → Instalar fichero → el `.face`.

Usa un **ID de 9 dígitos distinto** por esfera. El móvil cachea la preview por ID.

## Siguiente paso

Autoría de widgets, sources y botones: [`AUTHORING.md`](AUTHORING.md).
Guía usuario ES: [`../LEEME.md`](../LEEME.md).
