rm -f progress.txt
while true; do
    echo "$(ls -1 *.slcio | wc -l) $(date +%Y_%m_%d_%Hh%Mm%Ss)" >> progress.txt
    sleep 60
done
