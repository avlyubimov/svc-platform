# Platform exports

## iOS

Use `ios/AppIcon-1024.png` as the single-size AppIcon source in the generated
Xcode asset catalog. iOS applies its own icon mask; do not round or mask the
source again.

## Android

Legacy launcher exports:

- `mipmap-mdpi`: 48 px
- `mipmap-hdpi`: 72 px
- `mipmap-xhdpi`: 96 px
- `mipmap-xxhdpi`: 144 px
- `mipmap-xxxhdpi`: 192 px

`play-store/icon-512.png` is the store artwork.

For an adaptive icon, use:

- foreground: `android/adaptive/ic_launcher_foreground.svg`;
- background: `#05080C`.

The final Android resource conversion should be performed by the application
build so Android Studio can generate the required VectorDrawable and mask
previews.
