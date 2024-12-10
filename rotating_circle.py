from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout


class RotationThread(QThread):
    update_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.angle = 0
        self.running = False  # Initially, the rotation is not running

    def run(self):
        """Run the rotation logic in a separate thread."""
        while self.running:
            self.angle += 2
            if self.angle >= 360:
                self.angle = 0
            self.update_signal.emit(self.angle)  # Emit the updated angle
            self.msleep(30)  # Sleep for 30 milliseconds

    def stop_rotation(self):
        """Stop the rotation thread."""
        self.running = False

    def start_rotation(self):
        """Start the rotation thread."""
        self.running = True
        self.start()  # Start the thread when calling start_rotation


class RotatingCircleWidget(QWidget):
    def __init__(self, radius=50, size=400):
        super().__init__()

        # Set default size and title for the widget
        self.setWindowTitle("Rotating Circle")
        self.setGeometry(100, 100, size, size)

        self.angle = 0  # Starting angle for rotation
        self.radius = radius  # Set circle radius directly
        self.segments_color = None  # Used to control color change

        # Create the rotation thread, but don't start it automatically
        self.rotation_thread = RotationThread()
        self.rotation_thread.update_signal.connect(self.update_angle)

    def update_angle(self, angle):
        """Update the rotation angle from the separate thread."""
        self.angle = angle
        self.update()  # Request a repaint

    def paintEvent(self, event):
        """Paint the rotating circle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = self.rect().center()
        num_segments = 12  # Number of segments in the circle
        segment_angle = 360 / num_segments

        # Draw the rotating circle with segments
        for i in range(num_segments):
            # If segments_color is None, continue rotating with changing colors
            if self.segments_color is None:
                painter.setBrush(QColor((i * 20) % 255, (i * 30) % 255, (i * 40) % 255))
            else:
                # If segments_color is set, make all segments the same color (green)
                painter.setBrush(self.segments_color)

            painter.setPen(Qt.GlobalColor.transparent)

            # Define the start and end angles for each segment
            start_angle = int((self.angle + i * segment_angle) * 16)  # Ensure the angle is an integer
            span_angle = int(segment_angle * 16)  # Ensure the span angle is an integer

            # Use QRectF for the rectangle, adjusted for the radius
            painter.drawPie(
                QRectF(center.x() - self.radius, center.y() - self.radius, 2 * self.radius, 2 * self.radius),
                start_angle, span_angle)

    def insert_into_layout(self, layout):
        """Insert the rotating circle widget into a given layout."""
        layout.addWidget(self)

    def stop_rotation(self):
        """Stop the rotation and change all segments to green."""
        self.rotation_thread.stop_rotation()  # Stop the rotation thread
        self.segments_color = QColor(0, 255, 0)  # Change color to green
        self.update()  # Request a repaint to update the color

    def start_rotation(self):
        """Start the rotation and reset the segment colors."""
        self.segments_color = None  # Reset color to allow rotation with dynamic colors
        self.rotation_thread.start_rotation()  # Start the rotation thread
        self.update()  # Request a repaint to resume the rotation
