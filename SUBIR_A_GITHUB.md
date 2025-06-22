# Cómo subir RT-11 Extractor a GitHub

## Pasos para crear el repositorio en GitHub

1. **Ve a GitHub.com** y haz login
2. **Clic en el botón "+" (New repository)**
3. **Nombre del repositorio**: `rt11-extractor` (o el que prefieras)
4. **Descripción**: `Cross-platform RT-11 file system extractor with GUI`
5. **Configuración**:
   - ✅ Public (recomendado para GitHub Actions gratuito)
   - ❌ NO marques "Add a README file" (ya tenemos uno)
   - ❌ NO marques "Add .gitignore" (ya tenemos uno)
   - ❌ NO marques "Choose a license" (añadir después si quieres)

6. **Clic en "Create repository"**

## Comandos para subir desde tu terminal

Una vez creado el repositorio en GitHub, ejecuta estos comandos en tu terminal:

```bash
# Configurar el repositorio remoto (reemplaza 'tu-usuario' con tu nombre de usuario de GitHub)
git remote add origin https://github.com/tu-usuario/rt11-extractor.git

# Cambiar el nombre de la rama principal a 'main' (si es necesario)
git branch -M main

# Subir todo a GitHub
git push -u origin main
```

## Resultado después de subir

Después de subir, GitHub automáticamente:

1. **Detectará el workflow** en `.github/workflows/build-executables.yml`
2. **Ejecutará el primer build** automáticamente 
3. **Generará ejecutables** para todas las plataformas

## Cómo verificar que funciona

1. **Ve a tu repositorio** en GitHub
2. **Clic en la pestaña "Actions"**
3. **Deberías ver** "Build RT-11 Extractor Executables" ejecutándose
4. **Espera ~15 minutos** para que termine
5. **Descarga los artifacts** generados

## Crear tu primer Release

Para crear un release oficial con todos los ejecutables:

```bash
# Crear y subir un tag
git tag v1.0.0
git push origin v1.0.0
```

Esto creará automáticamente un Release en GitHub con todos los ejecutables listos para descargar.

## Estructura final en GitHub

Tu repositorio tendrá:
```
rt11-extractor/
├── .github/workflows/build-executables.yml  # Workflow de compilación
├── rt11extract_gui.py                       # Código fuente principal
├── rt11extract                              # CLI
├── images.png, icon.ico                     # Recursos
├── README.md                                # Documentación
├── GITHUB_ACTIONS_BUILD.md                  # Instrucciones del workflow
└── [otros archivos de documentación]
```

## Ventajas de tenerlo en GitHub

✅ **Compilación automática** en cada push
✅ **Ejecutables para todas las plataformas** sin configurar nada
✅ **Releases automáticos** cuando creas tags
✅ **Distribución fácil** via GitHub Releases
✅ **Backup automático** de tu código
✅ **Colaboración** si quieres que otros contribuyan
✅ **GitHub Actions gratis** para repositorios públicos

## ¿Problemas?

Si tienes problemas:

1. **Verifica los logs** en Actions > [nombre del build] > [job específico]
2. **Revisa que todos los archivos** estén en el repositorio
3. **Asegúrate** de que el repositorio sea público (para Actions gratuito)

## Próximos pasos

Una vez subido y funcionando:
- Los builds se ejecutarán automáticamente en cada push
- Puedes crear releases con `git tag v1.x.x && git push origin v1.x.x`
- Los usuarios podrán descargar ejecutables directamente desde GitHub
