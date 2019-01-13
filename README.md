[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg?style=flat-square)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=LWF3MAPZNPDQU&source=url)
# Clarisse Survival Kit

![Header Image](http://remuno.nl/wp-content/uploads/2019/01/mountain_cave.jpg)

>Clarisse Survival Kit(***CSK***) is a set of Python functions for Clarisse to automate repetitive processes such as importing generic textures, Megascans assets and mixing materials.

## Installation

CSK requires Python 2.7 to be installed.

**Make sure Clarisse is not running while installing the kit**

**NOTICE:** OSX users should open their **clarisse.env** file and locate their Python installation before running one of the following commands. The commands must be run with the Python installation that is used by Clarisse.

Download the zip by clicking the big green button, extract the files and run the following command via the command line:
```sh
$ python setup.py install
```

Or if you have pip installed you can download or link directly to the tarball in the dist folder and use the following command to set it up:
```sh
$ pip install .\clarisse_survival_kit-0.0.1.tar.gz
```

The shelf will automatically be updated and backed up. If the installation does not install the shelf correctly you can find a shelf_installation.log file in your Isotropix/VERSION/ user folder.

On Windows you can find the shelf_installation.log file here:

>C:/Users/**YOUR_USERNAME**/AppData/Roaming/Isotropix/Clarisse/**VERSION**

On Linux you can find it here:

>/home/**YOUR_USERNAME**/.isotropix/**VERSION**

On Mac you can find it here:

>/Users/**YOUR_USERNAME**/Library/Preferences/Isotropix/Clarisse/**VERSION**


## Features
*When a script asks you to select a material either select the PhysicalStandard material or its parent context*

The kit provides the following scripts:
### Import Asset
  - Import a Megascans asset. Meshes will automatically have their materials assigned when imported as .obj. Alembic(.abc) files will be imported as references. 3D assets such as  3d models, plants & atlases will also have a shading rule created for them. 
  - Import generic textures such as Substance. You can specify which textures should be interpreted as sRGB if needed. Custom rules can be added/modified in the settings.py file. TX or UDIM files will be converted to Streamed Maps.

### Mix Multiple Surfaces
 - Creates a PhysicalBlend between one or more base surfaces and a cover surface(like dirt/snow). All selectors except displacement are instanced so you can manipulate multiple mixed surfaces at once. With this powerful script you can transform a whole scene into a snow covered one with ease.
 - Masking features:
   * Height blend: Mixes the materials based on Y elevation. Handy for shore lines.
   * Displacement blend: Checks which displacement map has higher elevation than the other. You can invert the selector or add both layers on top of each other.
   * Slope blend: Mixes two materials based on slope angle. 
   * Triplanar blend: Uses triplanar mapping for the mask. By default the top facing(Y+) angle is masked.
   * Scope blend: A scope object is automatically created to quickly mask things out.
   * Occlusion blend: You can use Ambient Occlusion to blend the materials. Has a huge impact on performance when used with Displacement.
   * Fractal blend: If any other selectors are active the Fractal blend selector will be overlayed on top to break up the masking in the transition areas.

### Replace Surface
You can quickly replace the selected surface or change the mapping settings. If you're replacing a material that was used in a surface mix it will also update.

### Toggle Surface Complexity
Swaps out the selected material temporarily with a simple PhysicalDiffuse material. When you rerun the command on the selected PhysicalStandard material or its parent context it converts it back to the original state.

### Moisten Surface
Adds a wet layer on top of the selected material. Several masking options are available.

### Tint Surface
Adds a blend texture which can be used to colorize the selected surface so it matches better with other surfaces.

### Texture(s) to Triplanar
Converts the selected textures to triplanar.

### Blur Selected Texture(s)
Blurs the selected texture with a custom radius.

### Generate Decimated Pointcloud on Geometry
Generates a GeometryPointCloud or GeometryPointUvSampler on the selected object. Has several masking options for decimating the point cloud.

[Check out the video on Vimeo](https://vimeo.com/310524037)

### Import Megascans Library
Import the whole library or specified categories. If you need individual assets use the Import Asset script. If you import 3D assets make sure you import them in a context that is currently not rendered inside your viewport. Otherwise it will try to render all objects.

### Custom Settings
Locate the python package inside your site-packages folder. On windows the default path is:
> C:\Python27\Lib\site-packages\clarisse_survival_kit

You can manually make a folder inside that folder called ***user*** and create a **\_\_init\_\_.py** file and **user_settings.py** inside the user folder.

**OR** 

If you don't want to do that run the script once by clicking any of the buttons in the shelf and this folder and files are automatically generated for you.

All variables from the settings.py file can be copied over to and customized within the user_settings.py file inside your user folder. **Don't overwrite the settings.py file**. This file will be overwritten once you reinstall or upgrade.

# Changelog

- **13-01-19** Added logging.
- **13-01-19** Added user_settings.py for overriding settings. 
- **13-01-19** Fixed many bugs and tweaked usability.
- **12-01-19** Added multi mix feature.


# TODO
- Add a new surface to an existing multi mix.
- Preview file import.

Got any ideas? Did I miss anything important? Let me know.

# Thank you
[Aleks Katunar](https://github.com/ddesmond) was really kind to help me test out the script and for becoming a collaborator.

***Isotropix*** for their support and for creating Clarisse.

# License
GNU GPLV3
