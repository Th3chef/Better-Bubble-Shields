// hd2raw: minimal fast lister/extractor built on filediver's stingray package.
// usage: hd2raw <gamedata> index <out.tsv>
//
//	hd2raw <gamedata> get <outdir> <namehex.typehex>...
//	hd2raw <gamedata> grep <typehex> <hexpattern>[,<hexpattern>...]   (searches main data of all files of a type)
//	hd2raw <gamedata> serve        (reads "index ..." / "get ..." lines on stdin, answers "ok <n>" or "error <msg>";
//	                                the game's file table is read once for the whole session)
//
// Exit code 1 on any error (missing files included).
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/xypwn/filediver/hashes"
	"github.com/xypwn/filediver/stingray"
)

func ph(s string) (stingray.Hash, error) {
	v, err := strconv.ParseUint(strings.TrimPrefix(s, "0x"), 16, 64)
	return stingray.Hash{Value: v}, err
}

type tool struct {
	d     *stingray.DataDir
	names map[uint64]string
}

func (t *tool) nm(h stingray.Hash) string { return t.names[h.Value] }

func (t *tool) index(out string) (int, error) {
	f, err := os.Create(out)
	if err != nil {
		return 0, err
	}
	defer f.Close()
	w := bufio.NewWriter(f)
	for id, infos := range t.d.Files {
		var arcs []string
		for _, fi := range infos {
			arcs = append(arcs, fmt.Sprintf("%016x", fi.ArchiveID.Value))
		}
		fi := infos[0]
		fmt.Fprintf(w, "%016x\t%016x\t%s\t%s\t%d\t%d\t%d\t%s\n", id.Name.Value, id.Type.Value, t.nm(id.Name), t.nm(id.Type),
			fi.Files[0].Size, fi.Files[1].Size, fi.Files[2].Size, strings.Join(arcs, ","))
	}
	return len(t.d.Files), w.Flush()
}

func (t *tool) get(out string, ids []string) (int, error) {
	if err := os.MkdirAll(out, 0755); err != nil {
		return 0, err
	}
	n := 0
	var missing []string
	for _, a := range ids {
		p := strings.SplitN(a, ".", 2)
		if len(p) != 2 {
			return n, fmt.Errorf("bad id %q (want name.type)", a)
		}
		name, err1 := ph(p[0])
		typ, err2 := ph(p[1])
		if err1 != nil || err2 != nil {
			return n, fmt.Errorf("bad id %q", a)
		}
		id := stingray.NewFileID(name, typ)
		if len(t.d.Files[id]) == 0 {
			missing = append(missing, a)
			continue
		}
		for k, ext := range []string{"main", "stream", "gpu"} {
			b, err := t.d.Read(id, stingray.DataType(k))
			if err == stingray.ErrFileDataTypeNotExist {
				continue
			}
			if err != nil {
				return n, fmt.Errorf("%s %s: %v", a, ext, err)
			}
			if err := os.WriteFile(filepath.Join(out, fmt.Sprintf("0x%016x.%s.%s", id.Name.Value, p[1], ext)), b, 0644); err != nil {
				return n, err
			}
		}
		n++
	}
	if len(missing) > 0 {
		return n, fmt.Errorf("not in the game: %s", strings.Join(missing, " "))
	}
	return n, nil
}

func (t *tool) grep(typS, patS string) error {
	typ, err := ph(typS)
	if err != nil {
		return err
	}
	var pats [][]byte
	for _, s := range strings.Split(patS, ",") {
		b, err := hex.DecodeString(s)
		if err != nil {
			return err
		}
		pats = append(pats, b)
	}
	for id := range t.d.Files {
		if id.Type != typ {
			continue
		}
		b, err := t.d.Read(id, stingray.DataMain)
		if err != nil {
			continue
		}
		for i, p := range pats {
			if bytes.Contains(b, p) {
				fmt.Printf("%016x\t%s\tpat%d\n", id.Name.Value, t.nm(id.Name), i)
			}
		}
	}
	return nil
}

func (t *tool) run(args []string) (int, error) {
	if len(args) == 0 {
		return 0, fmt.Errorf("no command")
	}
	switch args[0] {
	case "index":
		if len(args) != 2 {
			return 0, fmt.Errorf("usage: index <out.tsv>")
		}
		return t.index(args[1])
	case "get":
		if len(args) < 2 {
			return 0, fmt.Errorf("usage: get <outdir> <id.type>...")
		}
		return t.get(args[1], args[2:])
	case "grep":
		if len(args) != 3 {
			return 0, fmt.Errorf("usage: grep <typehex> <hexpatterns>")
		}
		return 0, t.grep(args[1], args[2])
	}
	return 0, fmt.Errorf("unknown command %q", args[0])
}

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintln(os.Stderr, "usage: hd2raw <game data folder> index|get|grep|serve ...")
		os.Exit(1)
	}
	d, err := stingray.OpenDataDir(context.Background(), os.Args[1], nil)
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
	t := &tool{d: d, names: map[uint64]string{}}
	for _, h := range hashes.ParseHashes(hashes.Hashes) {
		t.names[stingray.Sum(h).Value] = h
	}
	if os.Args[2] == "serve" {
		sc := bufio.NewScanner(os.Stdin)
		sc.Buffer(make([]byte, 1<<20), 1<<24)
		fmt.Println("ready")
		for sc.Scan() {
			n, err := t.run(strings.Fields(sc.Text()))
			if err != nil {
				fmt.Println("error", err)
			} else {
				fmt.Println("ok", n)
			}
		}
		return
	}
	if _, err := t.run(os.Args[2:]); err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
}
