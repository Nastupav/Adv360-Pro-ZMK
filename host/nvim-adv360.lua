-- Advantage360 J/K/L/; pane navigation.
-- Ctrl+Shift letters are intentionally avoided because many terminals collapse
-- them to the same control bytes as Ctrl+letter.

vim.keymap.set('n', '<C-j>', '<C-w><C-h>', { desc = 'Pane focus left' })
vim.keymap.set('n', '<C-k>', '<C-w><C-j>', { desc = 'Pane focus down' })
vim.keymap.set('n', '<C-l>', '<C-w><C-k>', { desc = 'Pane focus up' })
vim.keymap.set('n', '<C-;>', '<C-w><C-l>', { desc = 'Pane focus right' })

vim.keymap.set('n', '<leader>wJ', '<C-w>H', { desc = 'Move pane left' })
vim.keymap.set('n', '<leader>wK', '<C-w>J', { desc = 'Move pane down' })
vim.keymap.set('n', '<leader>wL', '<C-w>K', { desc = 'Move pane up' })
vim.keymap.set('n', '<leader>w;', '<C-w>L', { desc = 'Move pane right' })

vim.keymap.set('t', '<C-j>', '<C-\\><C-n><C-w><C-h>', { desc = 'Terminal pane focus left' })
vim.keymap.set('t', '<C-k>', '<C-\\><C-n><C-w><C-j>', { desc = 'Terminal pane focus down' })
vim.keymap.set('t', '<C-l>', '<C-\\><C-n><C-w><C-k>', { desc = 'Terminal pane focus up' })
vim.keymap.set('t', '<C-;>', '<C-\\><C-n><C-w><C-l>', { desc = 'Terminal pane focus right' })
