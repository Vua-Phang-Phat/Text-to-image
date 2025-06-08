class ImageResult {
  final String? base64;
  final String? url;

  ImageResult({this.base64, this.url});

  factory ImageResult.fromBase64(String base64) {
    return ImageResult(base64: base64, url: null);
  }

  factory ImageResult.fromUrl(String url) {
    return ImageResult(base64: null, url: url);
  }
}