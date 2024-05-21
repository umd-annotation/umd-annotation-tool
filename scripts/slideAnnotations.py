
import json
import os
import click

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output_file', type=click.Path(), default=None, help='Output file name. Defaults to input file name with _modified before the extension.')
@click.option('--shift', type=int, required=True, help='Amount to shift the begin/end and frame values by.')

def adjust_frames(input_file, output_file, shift):
    """Adjust the begin/end and frame values in the JSON file by the specified shift amount."""
    # Determine the output file name if not provided
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_modified{ext}"

    with open(input_file, 'r') as infile:
        data = json.load(infile)

    # Adjust track begin, end, and feature frames
    for track in data.get('tracks', {}).values():
        track['begin'] += shift
        track['end'] += shift
        for feature in track['features']:
            feature['frame'] += shift

    # Adjust group begin, end, and member ranges
    for group in data.get('groups', {}).values():
        group['begin'] += shift
        group['end'] += shift
        for member in group['members'].values():
            member['ranges'] = [[start + shift, end + shift] for start, end in member['ranges']]

    with open(output_file, 'w') as outfile:
        json.dump(data, outfile, indent=2)
        click.echo(f"Adjusted JSON data saved to {output_file}")

if __name__ == '__main__':
    adjust_frames()
