    if(m[2]==0x32 && !m[0x42ca] && (m[0x7f]!=255 || m[0x82]!=127)){
        ++m[0x16];
        source_contact_frame(0x15bc);
        source_sprite_publish();
        source_field_timers();
        m[0x98]=source_direction(actor_input);m[0x9b]=(unsigned char)!(actor_input&BL_FIRE);
        m[0xdc00]=m[0xdc01]=255;
        m[0xdc02]=m[0x2005];m[0xdc03]=m[0x2006];
        if(!m[0x104] || (!(m[0x105]&128) && ((m[0x98]|m[0x99])!=15 || !(m[0x9b]&m[0x9c]))))m[0x82]=0;
        actor_irq_stop=0;
    }
