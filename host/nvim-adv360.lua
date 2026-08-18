-- Advantage360 editor-pane carriers.
-- NAV+Y/U/I/O emits F21/F22/F23/F24 for left/down/up/right. These
-- non-printing keys remain distinct in Ghostty terminfo and avoid Ctrl+;
-- ambiguity. The same carrier order is used by VS Code.

vim.keymap.set('n', '<F21>', '<C-w>h', { desc = 'Pane focus left' })
vim.keymap.set('n', '<F22>', '<C-w>j', { desc = 'Pane focus down' })
vim.keymap.set('n', '<F23>', '<C-w>k', { desc = 'Pane focus up' })
vim.keymap.set('n', '<F24>', '<C-w>l', { desc = 'Pane focus right' })

vim.keymap.set('i', '<F21>', '<C-o><C-w>h', { desc = 'Pane focus left' })
vim.keymap.set('i', '<F22>', '<C-o><C-w>j', { desc = 'Pane focus down' })
vim.keymap.set('i', '<F23>', '<C-o><C-w>k', { desc = 'Pane focus up' })
vim.keymap.set('i', '<F24>', '<C-o><C-w>l', { desc = 'Pane focus right' })

vim.keymap.set('t', '<F21>', '<C-\\><C-n><C-w>h', { desc = 'Terminal pane focus left' })
vim.keymap.set('t', '<F22>', '<C-\\><C-n><C-w>j', { desc = 'Terminal pane focus down' })
vim.keymap.set('t', '<F23>', '<C-\\><C-n><C-w>k', { desc = 'Terminal pane focus up' })
vim.keymap.set('t', '<F24>', '<C-\\><C-n><C-w>l', { desc = 'Terminal pane focus right' })

vim.keymap.set('n', '<leader>wJ', '<C-w>H', { desc = 'Move pane left' })
vim.keymap.set('n', '<leader>wK', '<C-w>J', { desc = 'Move pane down' })
vim.keymap.set('n', '<leader>wL', '<C-w>K', { desc = 'Move pane up' })
vim.keymap.set('n', '<leader>w;', '<C-w>L', { desc = 'Move pane right' })
