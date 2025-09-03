function downloadQr() {
    var dv = document.getElementById('shareqrcode');
    var im = dv.querySelector('img');
    var dl = document.createElement('a');
    dl.download = '{{ the_site_name }} - QR Code.png';
    dl.href = im.src;
    dl.click();
}
