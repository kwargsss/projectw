import disnake

from datetime import datetime

def build_v1_embed(data: dict) -> disnake.Embed:
    embed = disnake.Embed()
    if data.get('title'): embed.title = data['title']
    if data.get('description'): embed.description = data['description']
    if data.get('url'): embed.url = data['url']
    
    color_hex = data.get('color', '#5865F2').replace('#', '')
    if color_hex: embed.color = int(color_hex, 16)
    
    if data.get('author_name'):
        embed.set_author(
            name=data['author_name'],
            icon_url=data.get('author_icon') if data.get('author_icon') else None,
            url=data.get('author_url') if data.get('author_url') else None
        )
    
    if data.get('image_url'): embed.set_image(url=data['image_url'])
    if data.get('thumbnail_url'): embed.set_thumbnail(url=data['thumbnail_url'])
    
    if data.get('footer'):
        embed.set_footer(text=data['footer']['text'], icon_url=data['footer'].get('icon_url'))
        embed.timestamp = datetime.utcnow()
    
    for field in data.get('fields', []):
        if field.get('name') and field.get('value'):
            embed.add_field(name=field['name'], value=field['value'], inline=field.get('inline', False))
            
    return embed


def build_v2_components(data: dict) -> list[disnake.ui.Component]:
    components_list = []
    
    for block in data.get('blocks', []):
        b_type = block.get('type')
        
        if b_type == 'text_display' and block.get('content'):
            components_list.append(disnake.ui.TextDisplay(block['content']))
                
        elif b_type == 'media_gallery' and block.get('url'):
            media_obj = disnake.UnfurledMediaItem(url=block['url'])
            components_list.append(
                disnake.ui.MediaGallery(
                    disnake.MediaGalleryItem(media=media_obj, description=block.get('description', ''))
                )
            )
                
        elif b_type == 'separator':
            components_list.append(disnake.ui.Separator(divider=True))
            
        elif b_type == 'section':
            accessory = None
            if block.get('button_label') and block.get('button_url'):
                accessory = disnake.ui.Button(
                    style=disnake.ButtonStyle.link,
                    label=block['button_label'],
                    url=block['button_url']
                )
            if block.get('content'):
                components_list.append(disnake.ui.Section(
                    disnake.ui.TextDisplay(block['content']),
                    accessory=accessory
                ))
                
        elif b_type == 'file' and block.get('url'):
            components_list.append(disnake.ui.File(file={"url": block['url']}, spoiler=False))

    if data.get('footer'):
        components_list.append(disnake.ui.Separator(divider=True))
        now_ts = int(datetime.now().timestamp())
        footer_text = f"{data['footer']['text']} • <t:{now_ts}:f>"
        components_list.append(disnake.ui.TextDisplay(footer_text))
    
    color_hex = data.get('color', '#5865F2').lstrip('#')
    container = disnake.ui.Container(
        *components_list,
        accent_colour=disnake.Colour(int(color_hex, 16) if color_hex else 0x5865F2),
        spoiler=False
    )
    return [container]