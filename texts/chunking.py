import os
import glob

def chunk(file):
    with open(file, 'r') as f:
        text = f.read()
    # chunk after 20 words, split by blank space
    text = text.split()
    chunks = [' '.join(text[i:i+20]) for i in range(0, len(text), 20)]
    # save chunks to the same file, separated by newlines
    with open(file, 'w') as f:
        f.write('\n\n'.join(chunks))


if __name__ == '__main__':
    # get txt files of the current folder
    files = glob.glob('*.txt')
    print(files)
    for file in files:
        chunk(file)
    print('All files chunked')