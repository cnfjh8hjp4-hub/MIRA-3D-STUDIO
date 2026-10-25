# Rendu « retarget_cmu.py » : refuse_controle

- Profil **PREVIEW**, moteur **cycles CPU**
- Machine : 4 cœurs, 15.6 Go RAM, GPU : aucun ; moteurs qui fonctionnent : cycles, eevee
- Réglages : 360x640, 8 échantillons
- Images : None au total, None reprises du cache, 0 rendues
- Estimation avant rendu : None min ; temps de rendu réel : 0.0 min
- Temps par image : None
- Durée totale (contrôle compris) : 0.0 min

## Contrôle qualité
Verdict : **refusé**
- [bloquant] Blender a échoué pendant l'inspection (code 0)
- [bloquant] Traceback (most recent call last):
  File "/home/runner/blender/4.2/scripts/addons_core/io_anim_bvh/__init__.py", line 132, in execute
    return import_bvh.load(context, report=self.report, **keywords)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/blender/4.2/scripts/addons_core/io_anim_bvh/import_bvh.py", line 667, in load
    bvh_nodes, bvh_frame_time, bvh_frame_count = read_bvh(
                                                 ^^^^^^^^^
  File "/home/runner/blender/4.2/scripts/addons_core/io_anim_bvh/import_bvh.py", line 101, in read_bvh
    file = open(file_path, 'r')
           ^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/MIRA-3D-STUDIO/MIRA-3D-STUDIO/cache/assets/cmu/02_01.bvh'
Location: /h
- [avertissement] Error: Error: Python: Traceback (most recent call last):
- [avertissement] Error: Python: Traceback (most recent call last):
- [avertissement] Error: [Errno 2] No such file or directory: '/home/runner/work/MIRA-3D-STUDIO/MIRA-3D-STUDIO/cache/assets/cmu/02_01.bvh'
