# * @author        Yasir Aris M <yasiramunandar@gmail.com>
# * @date          2025-07-04 09:12:27
# * @projectName   MissKatyPyro
# * Copyright ©YasirPedia All rights reserved

# Base Docker Using Debian 12 (Bookworm), Python 3.11.4
FROM yasirarism/misskaty-docker:free

# Set Hostname
ENV HOSTNAME yasir-server
# Copy Files
COPY . .
# Instal pip package
RUN pip3 install --no-cache-dir -r requirements.txt
# Expose Port 8080
EXPOSE 8000
# Set CMD Bot
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]