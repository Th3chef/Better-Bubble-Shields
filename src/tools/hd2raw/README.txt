hd2raw - a minimal, fast Helldivers 2 lister/extractor built on Filediver's own reader (github.com/xypwn/filediver,
package stingray). It skips the extra data Filediver's CLI loads on every run, so it indexes the game in seconds
even over slow network folders.
Build (Linux, Go 1.25+):
  git clone --depth 1 --branch v0.7.55 https://github.com/xypwn/filediver.git
  mkdir -p filediver/cmd/hd2raw && cp main.go filediver/cmd/hd2raw/
  cd filediver && go build -o hd2raw ./cmd/hd2raw
Use:
  hd2raw <game data folder> index out.tsv          (id, type, name, type name, main/stream/gpu sizes, archives)
  hd2raw <game data folder> get <outdir> <id.type>...
  hd2raw <game data folder> grep <typehex> <hexpattern>[,<hexpattern>...]
