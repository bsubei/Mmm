#Mmm: A simple terminal-based text editor

import sys, tty, termios, copy

class Editor:
    def __init__(self):
        self._lines = []
        self._cursor = Cursor(1, 1)
        with open("test.txt") as lines:
            for line in lines:
                self._lines.append(line.rstrip('\n'))      
        self._buffer = Buffer(self._lines)

    def run(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        try:
            tty.setraw(sys.stdin.fileno())
            while 1:
                self.render()
                self.handle_input()
        finally:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def handle_input(self):
        getch = _GetchUnix()
        char = getch()
        # Ctrl + Q
        if char == chr(17):
            sys.stdout.write("\r\n\033[37;41m{}\033[39;49m\r\n".format("QUIT"))
            sys.exit(0)
        # Ctrl + H
        elif char == chr(8):
            self._cursor = self._cursor.left(self._buffer)
        # Ctrl + J
        elif char == chr(10):
            self._cursor = self._cursor.down(self._buffer)
        # Ctrl + K
        elif char == chr(11):
            self._cursor = self._cursor.up(self._buffer)
        # Ctrl + L
        elif char == chr(12):
            self._cursor = self._cursor.right(self._buffer)
        # Return key
        elif char == "\r":
            self._buffer = self._buffer.split_line(self._cursor._row, self._cursor._col)
            self._cursor = self._cursor.down(self._buffer).move_to_col(0)
        # Backspace key
        elif char == chr(127): 
            if self._cursor._col > 0:
                self._buffer = self._buffer.delete(self._cursor._row, self._cursor._col - 1)
                self._cursor = self._cursor.left(self._buffer)
            elif self._cursor._col == 0 and self._cursor._row != 0:
                temp_cursor = self._cursor
                self._cursor = self._cursor.up(self._buffer).move_to_end(self._buffer)
                self._buffer = self._buffer.shift_line_up(temp_cursor._row)
        else:
            self._buffer = self._buffer.insert(char, self._cursor._row, self._cursor._col) 
            self._cursor = self._cursor.right(self._buffer)
                    
    def render(self):
        ANSI.clear_screen()
        ANSI.move_cursor(0, 0)
        self._buffer.render()
        ANSI.move_cursor(self._cursor._row, self._cursor._col)
        # Cursor move is buffered if i dont do this :/
        sys.stdout.flush() 
        
class Buffer:
    def __init__(self, lines):
        self._lines = lines
    
    def render(self):
        for line in self._lines:
            sys.stdout.write(line + "\r\n")
            #sys.stdout.flush() # Not required in raw mode apparently
    
    @property
    def line_count(self):
        return len(self._lines)
        
    def line_length(self, row):
        return len(self._lines[row])
        
    def insert(self, char, row, col):
        # Duplicate the buffer state
        #lines = []
        #for line in self._lines:
        #    lines.append(line)
        lines = copy.deepcopy(self._lines)
        # Insert the new char at the cursor position in the line
        lines[row] = lines[row][:col] + char + lines[row][col:]
        return Buffer(lines)
    
    def delete(self, row, col):
        lines = copy.deepcopy(self._lines)
        # delete the char at the cursor position in the line
        lines[row] = lines[row][:col] + lines[row][col+1:]
        return Buffer(lines)

    def split_line(self, row, col):
        lines = copy.deepcopy(self._lines)
        left_half = lines[row][:col]
        right_half = lines[row][col:]
        lines[row] = left_half
        lines.insert(row + 1, right_half)
        return Buffer(lines)

    def shift_line_up(self, row):
        lines = copy.deepcopy(self._lines)
        end_of_above_line = len(lines[row - 1]) + 1
        lines[row - 1] = lines[row - 1] + lines[row]
        del lines[row]
        return Buffer(lines)
    
class Cursor:
    def __init__(self, row = 0, col = 0):
        self._row = row
        self._col = col
    
    def left(self, buffer):
        return Cursor(self._row, self._col - 1).clamp(buffer)
    
    def down(self, buffer):
        return Cursor(self._row + 1, self._col).clamp(buffer)
        
    def up(self, buffer):
        return Cursor(self._row - 1, self._col).clamp(buffer)
        
    def right(self, buffer):
        return Cursor(self._row, self._col + 1).clamp(buffer)
    
    # Constrain cursor motion
    def clamp(self, buffer):
        # Prevent cursor motion beyond the last line
        self._row = sorted((0, self._row, buffer.line_count-1))[1]
        # Prevent cursor motion beyond one space after the last char in a line
        self._col = sorted((0, self._col, buffer.line_length(self._row)))[1]
        return Cursor(self._row, self._col)
    
    def move_to_col(self, col):
        return Cursor(self._row, 0)

    def move_to_end(self, buffer):
        return Cursor(self._row, buffer.line_length(self._row))

class ANSI:
    def clear_screen():
        sys.stdout.write("\033[2J")

    def move_cursor(row, col):
        sys.stdout.write("\033[{};{}H".format(row + 1, col + 1))

# Gets a single char input. Code copied from StackOverflow
class _GetchUnix:
    def __call__(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

e = Editor()
e.run()