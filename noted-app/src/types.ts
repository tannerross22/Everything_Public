export interface NoteFile {
  name: string       // filename without .md
  path: string       // full absolute path
  modifiedAt: number // unix timestamp
}

export interface NoteContent {
  name: string
  path: string
  content: string    // raw markdown
}

export interface GraphNode {
  id: string         // note name
  path?: string      // undefined if note doesn't exist yet
}

export interface GraphLink {
  source: string
  target: string
}

export interface FileTreeNode {
  name: string                   // filename or folder name
  type: 'file' | 'folder'       // whether it's a file or folder
  path: string                   // absolute path
  children?: FileTreeNode[]      // for folders, contains children
  modifiedAt?: number           // for files, modification time
}
