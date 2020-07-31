#!/usr/bin/env bash

recipients='jhon@example.com (John Doe)'
recipients+=',jane@example.com (Jane Doe)'
from='trilio@example.com (TrilioVault RHV Backup)'
smtp='mail.example.com'

search_pattern='Number of failed Snapshots last 24h  : '
rhv_report_folder='/root/rhv-reporting/overall_report'
subject='TrilioVault Backup'

latest() {
  local file latest
  for file in "${1:-.}"/*; do
    [[ $file -nt $latest ]] && latest=$file
  done
  printf '%s\n' "$latest"
}

newest_file=$(latest "$rhv_report_folder")
if ! find "$newest_file" -newermt '1 day ago' -exec false {} +; then
  number_of_failed_snapshots=$(
    grep -F "$search_pattern" "$newest_file" |
      grep -o '[^ ]*$'
  )
  if [[ $number_of_failed_snapshots -ne 0 ]]; then
    mail -s "$subject failed!" -r "$from" -S "smtp=$smtp" "$recipients" <<-EOF
			Check your Backups in RHV!
		EOF
  else
    mail -s "$subject success" -r "$from" -S "smtp=$smtp" "$recipients" <<-EOF
			RHV Backup OK
		EOF
  fi
else
  mail -s "$subject" -r "$from" -S "smtp=$smtp" "$recipients" <<-EOF
		No RHV Backups in the last 24 Hours!
	EOF
fi
