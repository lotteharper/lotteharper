def convert_video_anime(input_path, output_path):
    from shell.execute import run_command
    from django.conf import settings
    run_command('{}/venv/bin/python {}/pytorch-animeGAN/inference.py --weight hayao:v2 --src {} --out {} --batch-size 4'.format(str(settings.BASE_DIR), str(settings.BASE_DIR), input_path, output_path))
    return output_path
