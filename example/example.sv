`default_nettype none

module fsmFullyEncoded
    (input  logic       clock, reset_n,
     input  logic       snow, rain, cloud,
     input  logic [6:0] temp,
     output logic       a, b, c);

    enum logic [2:0] {JANUARY, FEBRUARY, MARCH, APRIL, MAY, JUNE, JULY} state, nextState;

    always_ff @(posedge clock, negedge reset_n)
        if (~reset_n)
            state <= JANUARY;
        else 
            state <= nextState;

    always_comb begin // next state generator
        unique case (state) 
            JANUARY: begin
                if (snow) begin
                    nextState = (temp > 30) ? JANUARY : FEBRUARY;
                end
                else if (temp > 50) begin
                    nextState = JULY;
                end
                else nextState = JUNE;
            end
            FEBRUARY: begin
                if (snow) begin
                    nextState = JANUARY;
                end
                else if (rain) begin
                    nextState = MARCH;
                end
                else begin
                    nextState = FEBRUARY; 
                end
            end
            MARCH: begin
                nextState = APRIL;
            end
            APRIL: begin
                if (clouds) begin
                    nextState = (rain) ? MAY : JANUARY;    
                end
                else if (snow) nextState = MARCH;
                else begin
                    nextState = APRIL;
                end
            end
            MAY: begin
                if (!clouds) nextState = JUNE;
                else begin
                    if (rain) begin
                        nextState = MARCH;
                    end
                    else begin
                        nextState = JULY;
                    end
                end
            end
            JUNE: begin
                if (!rain) begin
                    nextState = JULY;
                end
            end
            JULY: begin
                if (snow) nextState = JANUARY;
                else begin
                    if (rain) begin
                        nextState = MARCH;
                    end
                    else begin
                        if (temp > 80) begin
                            nextState = JULY;
                        end
                        else begin
                            nextState = JUNE;
                        end
                    end
                end
            end
        endcase
    end

    always_comb begin // output logic
        a = 0; b = 0; c = 0;
        unique case (state)
            JANUARY: begin
                a = 1;
            end
            FEBRUARY: begin
                a = 1;
                b = 1;
            end
            MARCH: begin
                a = 1;
                b = 1;
                c = 1;
            end
            APRIL: begin
                {b, c} = 2'b11;
            end
            MAY: begin
                a = 1;
                b = 1;
            end
            JUNE: begin
                {a, b, c} = 2'b110;
            end
            JULY: begin
                b = 1;
            end
        endcase
    end

endmodule: fsmFullyEncoded